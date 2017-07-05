=pod

=head1 NAME

SessionManagement - manage session for user (login ,logout)

=head1 SYNOPSIS

=head1 REQUIRES

Perl5, DBI, Digest::MD5

=head1 DESCRIPTION

Manage session for user login

=cut

package SessionManagement;

use strict;
use Carp qw (cluck confess croak);
use warnings;
use Error qw(:try);
use Error::Message;

use Config::Configuration;

use DBI;

use CGI;

use Digest::MD5 qw(md5_hex);


# Package constants
####################

=pod

=head1 CONSTANTS

B<$MAX_TRIES>: (integer)
maximum of tries to perform to get a new tracking ID.

B<$IP_HASH_SIZE>: (integer)
number of hex-digits used from IP hash to create a new trakcing ID.

B<$RANDOM_SIZE>: (integer)
number of random hex-digits used to create a new trakcing ID.

B<$SALT_LENGTH>: (integer)
length of the random salt used to protect passwords.

=cut

our $MAX_TRIES    = 10;
our $IP_HASH_SIZE = 16;
our $RANDOM_SIZE  = 16;
our $SALT_LENGTH  = 16;


# Package subs
###############

=pod

=head1 STATIC METHODS

=head2 logEvent

B<Description>: logs an event into the database.

B<ArgsCount>: 2-5

=over 4

=item $database_handle: (handle) (R)

a working (connected) database handle (DBI::db).

=item $engine: (string) (R)

event engine name.

=item $type: (string) (U)

event type. Can be one of: NOTICE, DEBUG, WARNING or ERROR. 

=item $event: (string) (U)

Event description to log without EOL char.

=item $more: (string) (U)

More details about the event log.

=back

=cut

sub logEvent
{
    my ($proto, $database_handle, $engine, $type, $event, $more) = @_;

    # check parameters
    if ((2 > @_) || (6 < @_) || (ref($database_handle) ne "DBI::db"))
    {
        confess "usage: SessionManagement->logEvent(database_handle, engine_name, event_type, event_text, more_info);";
    }

    if (not $database_handle)
    {
        cluck "could not log an event in database! No database handle.";
        return;
    }
    # engine name
    if (not $engine)
    {
        $engine = 'NONE';
    }
    $engine = substr($engine, 0, 8);
    # log type
    if (not $type)
    {
        $type = 'WARNING';
    }


    if (not $event)
    {
        $event = "Unknown event";
    }
    if (not $more)
    {
        $more = '';
    }
    # log event
    my $client_ip = $Configuration::REMOTE_CLIENT_IP;
    if (not $client_ip)
    {
        $client_ip = '';
    }
    # log query: id, date, type, engine, message, additional_data
    my $query = "INSERT INTO logs VALUES (DEFAULT, NOW(), '$type', '$engine', ?, ?);";
    # prepare the query
    my $statement_handle = $database_handle->prepare($query)
        or cluck "could not prepare statement \"$query\": " . DBI->errstr . "\n";
    # execute the query
    $statement_handle->execute($event, "Client IP: $client_ip\n$more")
        or cluck "could not log an event in database! Query failed.";
}



=pod

=head2 hashPassword

B<Description>:
compute and return the hash of a password.
If not salt is provided, a new one is generated (and returned).

B<ArgsCount>: 1 to 2

=over 4

=item $password: (string) R

a password string.

=item $salt: (string) U

a 16 bytes hash.

=back

B<Return>: (array)

the first element of the array is the password hash (string), the second is the salt used (string).

B<Caller>:
general

B<Example>:

    my ($pass_hash, $pass_salt) = SessionManagement->hashPassword("toto");
    my ($pass_hash_to_check) = SessionManagement->hashPassword("tutu", $pass_salt);
    if ($pass_hash ne $pass_hash_to_check)
    {
        print "toto is not tutu!\n";
    }

=cut

sub hashPassword
{
    my ($proto, $password, $salt) = @_;

    # check parameters
    if ((2 != @_) && (3 != @_))
    {
        confess "usage: my (\$pass_hash, \$pass_salt) = SessionManagement->hashPassword(password, pass_salt);";
    }

    # check salt
    if ((not $salt) || ($SALT_LENGTH != length($salt)))
    {
        # not a valid salt, generate one
        $salt = "";
        for (my $salt_index = 0; $SALT_LENGTH > $salt_index; ++$salt_index)
        {
            my $rand_val = int(rand()*16); # 16: hexadecimal digits
            if (10 > $rand_val)
            {
                $rand_val = chr(ord('0') + $rand_val);
            }
            else
            {
                $rand_val = chr(ord('a') + $rand_val - 10);
            }
            $salt .= $rand_val;
        }
    }

    my $pass_hash = md5_hex($password ^ $salt);
    return ($pass_hash, $salt);
}


=pod

=head2 logout

B<Description>:
logout a user and clear current session.

B<ArgsCount>: 1

=over 4

=item $base_cgi: (CGI::BaseCGI) R

current CGI object.

=back

B<Return>: (array of CGI::Cookie)

the logout cookie in an array or an empty array if user can't be logged out.

B<Caller>:
general

B<Example>:

    my $base_cgi = CGI::BaseCGI->new();
    my $logout_cookie = SessionManagement->logout($base_cgi);
    $base_cgi->headHTML({-cookie => $logout_cookie});
    ...

=cut

sub logout
{
    my ($proto, $base_cgi) = @_;

    # check parameters
    if (2 != @_)
    {
        confess "usage: my \$cookie = SessionManagement->logout(base_cgi);";
    }

    my $session = $base_cgi->getSession();

    my $cookie;

    if ($session)
    {
        # remove session cookie
        $cookie = $base_cgi->cookie(
                     -name    => 'CGISESSID',
                     -value   => 0,
                     -expires => 'Thursday, 1-Jan-1971 00:00:01 GMT',
                     -path    => "/"
                                  );
        # clear session
        $session->clear();
    }

    return [$cookie];
}




=pod

=head2 checkUserLogin

B<Description>:
try to login a user.

B<ArgsCount>: 1

=over 4

=item $base_cgi: (CGI::BaseCGI) R

the current CGI object containing the user submitted login and password.

=back

B<Return>: (array of CGI::Cookie)

the login cookie (and maybe a logout cookie) in an array or an empty array if
there was no user to log in.

B<Caller>:

general

=item Error::Message

thrown when an error occured during the login process. The message associated
should be displayed to the user.

=back


B<Example>:

    my $base_cgi = CGI::BaseCGI->new();
    my $cookie = SessionManagement->checkUserLogin($base_cgi);
    $base_cgi->headHTML({-cookie => $cookie});
    ...

=cut

sub checkUserLogin
{
    my ($proto, $base_cgi) = @_;

    # check parameters
    if (2 != @_)
    {
        confess "usage: my \$cookie = SessionManagement->checkUserLogin(base_cgi);";
    }

    my $session = $base_cgi -> getSession();
    my $cookie;
    my $cookies = [];

    my $policy_message = '';
    my $login = $base_cgi->param('login');
    my $password = $base_cgi->param('password');
    

    # check for login
    if ($login && $password)
    {
        # check user password from database
        try
        {
            # get client IP
            my $client_ip = $Configuration::REMOTE_CLIENT_IP;
            if (not $client_ip)
            {
                $client_ip = "0.0.0.0";
            }
            my @splited_ip = split(/\./, $client_ip);

	   my $user_data = "";
           my $user_access_data = "";
           my $flag = 2;
	  my $stored_info = `grep $login accounts`;
	   $stored_info =~s/\n//g;
	   $stored_info =~s/\r//g; 
  	   my ($username,$stored_passwd_hash,$salt,$flag) = split(":",$stored_info);
 
            # check if a valid account was found
            if ((not $username)
                || (not $salt))
            {
                $policy_message = "invalid account!!";
            }
            elsif ($Configuration::USER_FLAG_LOCKED eq $flag)
            {
                # check if a policy message was set in DB for that client
                if ($user_access_data && @$user_access_data && $user_access_data->[2])
                {
                    $policy_message = $user_access_data->[2];
                }
                else
                {
                    $policy_message = "invalid account!!!";
                }
            }
            elsif ($user_access_data
                   && @$user_access_data
                   && ($user_access_data->[1] >= $Configuration::MAX_LOGIN_TRIES)
                   && ($Configuration::ACCOUNT_LOCK_DELAY > $user_access_data->[0]))
            {
                # too many attempts and temporary lock delay is not over
                # check if a policy message was set ind DB for that client
                if ($user_access_data && @$user_access_data && $user_access_data->[2])
                {
                    $policy_message = $user_access_data->[2];
                }
                else
                {
                    $policy_message = "too many unsuccessful attempts, account temporary locked!";
                }
            }
            else
            {
                # check password
		my ($pass_hash_to_check) = SessionManagement->hashPassword($password, $salt);

                if ($stored_passwd_hash eq $pass_hash_to_check)
                {
                    # authentified
                    # check if user is already logged in and close previous session
                    my $logout_cookies = SessionManagement->logout($base_cgi);
                    if ($logout_cookies && @$logout_cookies)
                    {
                        push @$cookies, (@$logout_cookies);
                    }
                    $session->param("user_login",$username);
                    $session->param("priority", 2);
                    $session->param("rights",2);
                    $session->param("settings","");
                    $session->param("comments","");
                    if ($Configuration::USER_FLAG_ADMIN eq $flag)
                    {
                        $session->param("is_admin", '1');
                        $session->expire('+2h');
                    }
                    else
                    {
                        $session->param("is_admin", '0');
                        $session->expire('+24h');
                    }
                    $session->flush();
                    $cookie = $base_cgi->cookie(
                                 -name    => 'CGISESSID',
                                 -value   => $session->id(),
                                 -expires => '+24h',
                                 -path    => "/"
                                              );
                    push @$cookies, $cookie;
                    
                }
                else
                {
                    # authentification failed
                    $policy_message = "invalid login or password";
                    # increase access counter
                }
           }
        }
        otherwise
        {
            # failed
            $policy_message = "an error occured while accessing user accounts from database!";
            cluck shift;
        };
    }

    # check if an error occured during login process
    if ($policy_message)
    {
        throw Error::Message($policy_message);
    }

    return $cookies;
}





=pod

=head1 AUTHORS

Alexis DEREEPER (IRD), alexis.dereeper@ird.fr

=head1 VERSION

Date 10/12/2009

=head1 SEE ALSO

=cut

return 1; # package return
