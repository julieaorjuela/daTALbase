=pod

=head1 NAME

CGI::BaseCGI - Manage any CGI scripts

=head1 SYNOPSIS

my $base_cgi = CGI::BaseCGI -> new();

=head1 REQUIRES

CGI
CGI::Session
File::Copy

=head1 DESCRIPTION

This package enable to display a lot of common functions of CGI scripts

=cut

package CGI::BaseCGIBootstrap;

use strict;
use Carp qw (cluck confess croak);
use warnings;
use CGI::Session;
use File::Copy;
use Template;

use CGI qw(-private_tempfiles :standard);
use vars qw($fu);


use lib "..";

use Config::Configuration;

use base qw(CGI);



# Script global constants
####################

=pod

=head1 CONSTANTS

B<HOME_DIR>:  String, public

                   used to define the home directory of the web server

B<WEB_DIR>:  String, public

                   used to define the URL of the web server

=cut

my $WEB_DIR = $Configuration::WEB_DIR;
my $HOME_DIR = $Configuration::HOME_DIR;

# Script global variables
##########################

=pod

=head1 VARIABLES

B<cgi>:  String, public

                   the CGI

=cut


# Package subs
###############

=pod

=head1 STATIC METHODS

=head2 CONSTRUCTOR

B<Description>       : Creates a new instance.

B<ArgsCount>         : 0

B<Return>            : CGI::BaseCGI, a new instance.

B<Caller>            : general

B<Exception>         :

B<Example>           :

=cut

sub new
{
    my ($proto) = @_;
    my $class = ref($proto) || $proto;
    my $self = $class->SUPER::new();
    bless($self, $class);

    $self->{SESSION}        = undef;
    $self->{SESSION_COOKIE} = undef;

    # init session info
    CGI::Session->name('CGISESSID');
    $self->{SESSION} = new CGI::Session("driver:File", $self, {'Directory' => "/tmp"});
    # update expiration according to account type
    if ($self->{SESSION}->param("is_admin"))
    {
        # admin account
        $self->{SESSION}->expire('+2h');
    }
    else
    {
        # user account
        $self->{SESSION}->expire('+5h');
    }
    
    # check if session cookie is valid
    my $cookie = $self->cookie(-name => 'CGISESSID');
    if ((not $cookie) || ($self->{SESSION}->id() ne $cookie))
    {
        # reset session cookie
        $self->{SESSION_COOKIE} = $self->cookie(
                                      -name    => 'CGISESSID',
                                      -value   => $self->{SESSION}->id(),
                                      -path    => "/"
                                               );
    }
    elsif ($cookie && ($self->{SESSION}->id() eq $cookie))
    {
        # reset cookie expiration
        $self->{SESSION_COOKIE} = $self->cookie(
                                      -name    => 'CGISESSID',
                                      -value   => $self->{SESSION}->id(),
                                      -expires => '+24h',
                                      -path    => "/"
                                               );
    }
    return $self;
}

=pod

=head1 ACCESSORS

=cut


=pod

=head2 setTitle

B<Description>: set the title of the web page

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setTitle
{
    my ($self, $value) = @_;
    $self -> {TITLE} = $value;
}



=head2 getTitle

B<Description>: get the title of the web page

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getTitle
{
    my ($self) = @_;
   return $self -> {TITLE};
}

=pod

=head2 getSection

B<Description>: get the section for tab menu

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getSection
{
    my ($self) = @_;
   return $self -> {SECTION};
}

=pod

=head2 setSection

B<Description>: set the section for tab menu

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setSection
{
    my ($self, $value) = @_;
    $self -> {SECTION} = $value;
}


=pod

=head2 getRefreshing

B<Description>: get the refreshing link

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getRefreshing
{
    my ($self) = @_;
   return $self -> {REFRESHING};
}

=pod

=head2 setRefreshing

B<Description>: set the refreshing link

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setRefreshing
{
    my ($self, $value) = @_;
    $self -> {REFRESHING} = $value;
}



=head2 getHeading

B<Description>: get the heading of the web page

B<ArgsCount>  : 0

B<Return>     : String

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub getHeading
{
    my ($self) = @_;
   return $self -> {HEADING};
}

=pod

=head2 setHeading

B<Description>: set the heading of the web page

B<ArgsCount>  : 1

=over 4

=item arg    : String

=back

B<Return>     :  void

B<Caller>     : general

B<Exception>  :

B<Example>    :

=cut

sub setHeading
{
    my ($self, $value) = @_;
    $self -> {HEADING} = $value;
}


=pod

=head1 METHODS

=cut


#############################################################################################################################################################
#
#                                                                  head HTML
#
#############################################################################################################################################################

=pod

=head2 headHTML

B<Description>       : displays the head of the web page with lab logos

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub headHTML($$$$)
  {
    my $self = shift;
    my $section = $_[0];
    my $refreshing = $_[1];
    my $time_reloading = $_[2];
    my $use_highcharts = $_[3];
    my $style= "$Configuration::STYLE_DIR/style.css";
    my $menu_style= "$Configuration::STYLE_DIR/menu.css";
    my $onglet_style= "$Configuration::STYLE_DIR/onglets.css";
    my $results_style = "$Configuration::STYLE_DIR/results.css";
    
    

    my $title = $self -> getTitle();
    my $heading = $self -> getHeading();
    if ($refreshing)
      {
		print $self -> header(-refresh=>"$time_reloading; URL=$refreshing");
      }
    else
      {
		print $self -> header;
      }
      
    my $admin_access = $self->getSessionParam('is_admin');
	my $user_access = $self->getSessionParam('user_login');
	my $rights = $self->getSessionParam('rights');

	
   print $self->start_html(
                -title  => "daTALbase",
                -meta   => {'keywords'=>'TAL,xanthomonas','description'=>'TAL target finder'},
                -script => [{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-1.4.4.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-ui-1.8.9.custom.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/functions.js"}],
		-style  => [{'src'=>, "$Configuration::STYLE_DIR/style.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/jquery-ui-1.8.9.custom.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/biome.css",'type'=>'text/css'}]

        ); 
		   
	my $login_status = "";
	if ($user_access)
	{
		$login_status = "<a class=\"item-primary\" href=\"./login.cgi?logout=yes\"><font color=#ED2800>Log out</font></a>";
	}
	else
	{
		$login_status = "<a class=\"item-primary\" href=\"./login.cgi\">Login</a>";
	}
	print "<div id=\"page\">\n";
	
	
	my $bug_report_icone;
        if ($Configuration::BUG_REPORT_PAGE)
        {
                $bug_report_icone = "<a href=\"$Configuration::BUG_REPORT_PAGE\" target=\"_blank\"><img src=\"$Configuration::IMAGES_DIR/icone_question.png\" title=\"Report a problem\"/></a>";
        }

	
	
	my $style_display = qq~
	<style type="text/css">



</style>
~;
	print $style_display;
	

	
	
    print "<table><tr><td width=20></td><td><h2>$heading</font></h2>";
  }



=pod

=head2 headHTML

B<Description>       : displays the head of the web page with lab logos

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub headHTMLlight()
  {
    my $self = shift;
    my $style= "$Configuration::STYLE_DIR/style.css";
    my $menu_style= "$Configuration::STYLE_DIR/menu.css";
    my $onglet_style= "$Configuration::STYLE_DIR/onglets.css";
    my $results_style = "$Configuration::STYLE_DIR/results.css";
    
    my $title = $self -> getTitle();
    my $heading = $self -> getHeading();
	print $self -> header;

    print $self->start_html(
                -title  => "daTALbase",
                -meta   => {'keywords'=>'TAL,xanthomonas','description'=>'TAL target finder'},
		-script => [{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-1.4.4.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-ui-1.8.9.custom.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/functions.js"}],
		-style  => [{'src'=>, "$Configuration::STYLE_DIR/style.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/jquery-ui-1.8.9.custom.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/biome.css",'type'=>'text/css'}]

        );

      
  }
  
=pod

=head2 headHTMLCookie

B<Description>       : displays the head of the web page with lab logos

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub headHTMLCookie($)
  {
    my $self = shift;
    my $header_data = $_[0];
    my $style= "$Configuration::STYLE_DIR/style.css";
    my $menu_style= "$Configuration::STYLE_DIR/menu.css";
    my $onglet_style= "$Configuration::STYLE_DIR/onglets.css";
    
    my $title = $self -> getTitle();
    my $heading = $self -> getHeading();
    my $section = $self -> getSection();
    my $refreshing = $self -> getRefreshing();
    
    my $admin_access = $self->getSessionParam('is_admin');
	my $user_access = $self->getSessionParam('user_login');
	my $rights = $self->getSessionParam('rights');
    my $action = $self -> param('action');

    if ($header_data)
    {
        # check for session cookie
        if ($self->{SESSION_COOKIE})
        {
            if (exists $header_data->{'-cookie'})
            {
                if ('ARRAY' eq ref($header_data->{'-cookie'}))
                {
                    push @{$header_data->{'-cookie'}}, $self->{SESSION_COOKIE};
                }
                else
                {
                    $header_data->{'-cookie'} = [$self->{SESSION_COOKIE}, $header_data->{'-cookie'}];
                }
            }
            else
            {
                $header_data->{'-cookie'} = $self->{SESSION_COOKIE};
            }
        }
        if ($refreshing)
	    {
	    	$header_data->{'-refresh'} = "1; URL=$refreshing";
	    }
        print $self->header(%$header_data);
    }
    elsif ($self->{SESSION_COOKIE})
    {
    	if ($refreshing)
	    {
	    	print $self->header({'-cookie' => $self->{SESSION_COOKIE}, '-refresh' => "1; URL=$refreshing"});
	    }
	    else
	    {
	    	print $self->header({'-cookie' => $self->{SESSION_COOKIE}});
	    }
    }
    else
    {
        if ($refreshing)
	    {
			print $self -> header(-refresh=>"1; URL=$refreshing");
	    }
	    else
	    {
	    	print $self->header();
	    }
    }
   	if ($action){
	print $self->start_html(
                -title  => "daTALbase",
                -meta   => {'keywords'=>'TAL,xanthomonas','description'=>'TAL target finder'},
		-script => [{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-1.4.4.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-ui-1.8.9.custom.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/functions.js"}]

        );  
	}
	else{
		print $self->start_html(
                -title  => "daTALbase",
                -meta   => {'keywords'=>'TAL,xanthomonas','description'=>'TAL target finder'},
		-script => [{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-1.4.4.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-ui-1.8.9.custom.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/functions.js"}],
                -style  => [{'src'=>, "$Configuration::STYLE_DIR/style.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/jquery-ui-1.8.9.custom.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/biome.css",'type'=>'text/css'}]

        );
	}
	my $login_status = "";
	if ($user_access)
	{
		$login_status = "<a class=\"item-primary\" href=\"./login.cgi?logout=yes\"><font color=#ED2800>Log out</font></a>";
	}
	else
	{
		$login_status = "<a class=\"item-primary\" href=\"./login.cgi\">Login</a>";
	}
		   
	print "<div id=\"page\">\n";

	my $bug_report_icone;
	if ($Configuration::BUG_REPORT_PAGE)
	{
		$bug_report_icone = "<a href=\"$Configuration::BUG_REPORT_PAGE\" target=\"_blank\"><img src=\"$Configuration::IMAGES_DIR/icone_question.png\" title=\"Report a problem\"/></a>";
	}
	
	
	my $style_display = qq~
	<style type="text/css">

#results
{
font-family:"Trebuchet MS", Arial, Helvetica, sans-serif;
width:100%;
border-collapse:collapse;
}
#results td, #results th 
{
font-size:0.8em;
border:1px solid #848484;
padding:3px 7px 2px 7px;
}
#results th 
{
font-size:0.8em;
text-align:left;
padding-top:5px;
padding-bottom:4px;
background-color:#A4A4A4;
color:#fff;
}
#results tr.alt td 
{
color:#000;
background-color:#EAF2D3;
}

</style>
~;
	#print $style_display;

	
#    print "<table><tr><td width=20></td><td>$heading</font>";
  }
  
  
=pod

=head2 headHTMLsimple

B<Description>       : displays a simple head for web page

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub headHTMLsimple($$)
  {
    my $self = shift;
    my $section = $_[0];
    my $refreshing = $_[1];
    my $time_reloading = $_[2];
    my $style= "$Configuration::STYLE_DIR/style_simple.css";
    
    my $title = $self -> getTitle();
    my $heading = $self -> getHeading();



    if ($refreshing)
      {
		print $self -> header(-refresh=>"$time_reloading; URL=$refreshing");
      }
    else
      {
		print $self -> header;
      }

    print $self->start_html(
                -title  => "daTALbase",
                -meta   => {'keywords'=>'TAL,xanthomonas','description'=>'TAL target finder'},
		-script => [{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-1.4.4.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/jquery-ui-1.8.9.custom.min.js"},{'language'=>'javascript', 'src'=>"$Configuration::JAVASCRIPT_DIR/functions.js"}],
		-style  => [{'src'=>, "$Configuration::STYLE_DIR/style.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/jquery-ui-1.8.9.custom.css",'type'=>'text/css'},{'src'=>, "$Configuration::STYLE_DIR/biome.css",'type'=>'text/css'}]

        );

  }

  
#############################################################################################################################################################
#
#                                                                  end HTML
#
#############################################################################################################################################################

=pod

=head2 endHTML

B<Description>       : displays the base of the web page with genopole logos

B<ArgsCount>         : 0

B<Return>            : void

B<Exception>         :

=cut

sub endHTML
  {
    my $self=shift;
	
    print "</div>\n";
    print $self -> end_html();
  }
  
#############################################################################################################################################################
#
#                                                                  getSession
#
#############################################################################################################################################################

=pod

=head2 getSession

B<Description>       : create a new session if doesn't exist, and return the session id

B<ArgsCount>         : 0

B<Return>            : String

B<Exception>         :

=cut

sub getSession()
  {
    my $self = shift;
#    my $sessionId;
#    if( ! defined( $self -> param('session')))
#      {
#		my $session = new CGI::Session("driver:File", $sessionId, {Directory=>'/tmp'});
#		$sessionId = $session -> id();
#		$session -> delete();
#      }
#    else
#      {
#		$sessionId = $self -> param('session');
#      }
#    return $sessionId;
    return $self->{SESSION};
  }
  

  
=pod

=head2 getSessionParam

B<Description>:
returns the value of selected session parameter.

B<ArgsCount>: 1

=over 4

=item $param: (string) R

the parameter name.

=back

B<Return>: (string)

the parameter value.

=cut

sub getSessionParam
{
    my ($self, $param) = @_;

    # check parameters
    if (2 != @_)
    {
        confess "usage: my \$value = \$base_cgi->getSessionParam(parameter_name);";
    }

    my $value;
    if ($self->{SESSION} && $param)
    {
        $value = $self->{SESSION}->param($param);
    }
    return $value;
}


=pod

=head1 AUTHORS

Alexis DEREEPER (IRD), alexis.dereeper@ird.fr

=head1 VERSION

Version 0.1

=head1 SEE ALSO

=cut

return 1; # package return
