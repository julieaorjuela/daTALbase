=head1 NAME

Config::Configuration - Store all the constants (file and direcoriy names...)

=head1 SYNOPSIS

my $WEB_DIR = $Configuration::WEB_DIR;

=head1 REQUIRES

=head1 DESCRIPTION

This package enable to store all constants which can be used by any program or module : file and directory names...

=cut

package Configuration;

# Package constants
####################

=pod

=head1 CONSTANTS

B<HOMEPAGE>:  String, public

                   URL of the web page

B<WEB_DIR>:  String, public

                   used to define the URL of the web server

B<HOME_DIR>:  String, public

                   used to define the directory of the web server
=cut

########################### URL #########################
our $HOMEPAGE = "http://bioinfo-web.mpl.ird.fr/xantho/talbase/";
our $WEB_DIR  = "http://bioinfo-web.mpl.ird.fr/xantho/talbase";
our $SITE_SERVER = "bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase";

######################## directories ####################
our $HOME_DIR = "path_to_html";

our $CGI_DIR = "path_to_CGI";


our $JAVASCRIPT_DIR = $WEB_DIR . "/javascript";
our $IMAGES_DIR     = $WEB_DIR . "/images";
our $STYLE_DIR      = $WEB_DIR . "/styles";

our $EXECUTION_WEB_DIR = $WEB_DIR . "/tmp";
our $EXECUTION_DIR     = "/tmp";

our $CGI_WEB_DIR    = "http://url_cgi";

############# database connection ################
our $DATABASE_HOST = "hostname";
our $DATABASE_LOGIN = "talbase";
our $DATABASE_PASSWORD = "mypasswd";
our $DATABASE_NAME = "talbase";


our $MAX_LOGIN_TRIES = 2;
our $ACCOUNT_LOCK_DELAY = 120; # seconds
our $USER_FLAG_ADMIN = 1;
our $USER_FLAG_CONSULTATION = 2;
our $USER_FLAG_SUBMISSION = 3;
our $USER_FLAG_LOCKED = 5;

our $INSTANCE_TITLE = "Rice";
                   
=pod

=head1 AUTHORS

Alexis DEREEPER (IRD), alexis.dereeper@ird.fr

=head1 VERSION

Version 0.1

=head1 SEE ALSO

=cut

return 1; # package return
                   
