#!/usr/bin/perl

use strict;

use CGI;
use CGI::BaseCGIBootstrap;
use CGI::Session;
use DBI;
use Time::localtime;
use Time::Local;
use File::Copy;
use Config::Configuration;
use SessionManagement::SessionManagement;
use Carp qw (cluck confess croak);
use warnings;
use Error qw(:try);

#my $cgi = CGI->new;
my $base_cgi = CGI::BaseCGIBootstrap -> new();
$base_cgi -> setTitle("daTALbase");
$base_cgi -> setHeading("daTALbase");

my $cookie;
my $cookies = [];

if ($base_cgi->param("logout"))
{
        my $logout_cookies = SessionManagement->logout($base_cgi);
        push @$cookies, (@$logout_cookies);
}
my $policy_message = '';
try
{
        my $login_cookies = SessionManagement->checkUserLogin($base_cgi);
        push @$cookies, (@$login_cookies);
}
catch Error::Message with
{
        $policy_message = shift->text();
}
otherwise
{
};
my $admin_access = $base_cgi->getSessionParam('is_admin');
my $user_access = $base_cgi->getSessionParam('user_login');

if (@$cookies)
{
        $base_cgi->headHTMLCookie({-cookie => $cookies});
}
else
{
        $base_cgi->headHTMLCookie();
}

my $dbname = $Configuration::DATABASE_NAME;
my $host = $Configuration::DATABASE_HOST;
my $login = $Configuration::DATABASE_LOGIN;
my $password = $Configuration::DATABASE_PASSWORD;

my $database_handle = DBI->connect("DBI:mysql:database=" . $dbname . ";host=" . $host,$login,$password) || print "Database connection failed: $DBI::errstr";



my $header = qq~
<h1 align="center"><a href='./index.cgi'>daTALbase - Database for <abbr title='Transcription Activator Like Effector'>TAL Effectors</abbr> analysis</a></h1>
<h1 align="center"><i>$Configuration::INSTANCE_TITLE</i></h1>
~;

my $footer = qq~
<br/>
<hr/>
<p>
<div align="center">
<a href="http://www.ird.fr" target="_blank"><img alt="IRD logo" src="$Configuration::IMAGES_DIR/logo_ird.gif"/></a>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<a href="http://umr-ipme.ird.fr/" target="_blank"><img alt="IPME logo" src="$Configuration::IMAGES_DIR/IPME_petit.png" height="46"/></a>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<a href="http://www.southgreen.fr/" target="_blank"><img alt="Southgreen logo" src="$Configuration::IMAGES_DIR/logo_southgreen.png" height="46"/></a>
</div>
</p>
~;


my $session = $base_cgi ->param("session");
my $host_species = $base_cgi ->param("host_species");
my $bacteria_species = $base_cgi ->param("bacteria_species");
my $tals = $base_cgi ->param("tals");
my $genes = $base_cgi ->param("genes");
my $genes_from_EBEs = $base_cgi ->param("genes_from_EBEs");
my $genes_from_microarray = $base_cgi ->param("genes_from_microarray");


	
# params	   
my $SCRIPT_NAME = "login2.cgi";


if (!$session)
{
	$session = int(rand(10000000000000));
}
my $execution_dir = $Configuration::EXECUTION_DIR."/".$session;
if (!-d $execution_dir){
        mkdir($execution_dir);
}

my $config_viewer = qq~
'repartition' =>
        {
		"select_title" => "Number of TALs per strain",
                "per_chrom" => "off",
                "title" => "Number of TALs per strain",
                "type" => "pie",
                "stacking" => "off",
                "file" => "$execution_dir/repartition_tals.txt",
        },~;

open(my $T,">$execution_dir/$session.chrom_viewer.conf");
print $T $config_viewer;
close($T);

=pod

=head2 displayInputForm

B<Description>      : display a submitting form

B<ArgsCount>        : 0

B<Return>           : void

B<Exception>        :

B<Example>:

=cut

sub displayInputForm
{

	print $header;
	
	my $tab = qq~
<div id='content'>
<script>
\$(function() {
   \$( "#tabs" ).tabs();
});
</script>

<script>
<!--
\$(function(){
   \$('summary').mouseover(
      function(){ \$(this).parent().find("*").fadeIn(); }
   );
   \$('summary').mouseout(
      function(){ \$(this).parent().find("*:not(summary)").fadeOut();}// \$(this).fadeIn(); }
   );
});
-->
</script>
<div id='tabs'>
~;
	print $tab;
	# check if user is logged in
if ($user_access)
{
	print "You are logged on daTALbase.<br/><br/>";
	print "<br/><br/><a href=\"./$SCRIPT_NAME?logout=yes\" name=\"logout\">logout</a><br/>\n";
	print "<script type=\"text/javascript\">window.location.href = \"./index.cgi\"</script>";
}
else
{
	# not admin
    # display authentification form
    print "<font color=\"red\" size=\"4\"><i><b>Private Access</i></b></font><br/><br/>\n";
    print "This section requires authentification. <i>(reserved to partners and collaborators)</i><br/><br/>\n";

    my $login = $base_cgi->param('login');
    my $password = $base_cgi->param('password');

    # check if an invalid password or user account was provided
    if ((defined $admin_access) && (0 == $admin_access))
    {
        print "<span class=\"error\"><b>Error:</b> invalid account! (not admin)</span><br/>\n<br/>\n";
    }
    elsif ($login && $password)
    {
        print "<span class=\"error\"><b>Error:</b> $policy_message</span><br/>\n<br/>\n";
    }


    if ($policy_message !~ m/locked/i)
    {
        print "<form method=\"post\" action=\"./$SCRIPT_NAME\" id=\"loginForm\" name=\"admin_form\">\n";
        print "  Login: <input class=\"form-control\" type=\"text\" id=\"httpd_username\" name=\"login\" size=\"50\" alt=\"login\"/><br/>\n";
        print "  <br/>\n";
        print "  Password: <input class=\"form-control\" type=\"password\" id=\"httpd_password\" name=\"password\" size=\"50\" alt=\"password\"/><br/>\n";
        print "  <br/>\n";
        print "  <input type=\"submit\" class=\"btn btn-default\" id=\"login\" name=\"login\" value=\"Login\"/><br/>\n";
        print "</form>\n";

	my $form = qq~
<form class="form-inline">
<div class="form-group">
    <label class="sr-only" for="exampleInputEmail3">Email address</label>
    <input type="text" name="login" class="form-control" placeholder="Login">
  </div>
  <div class="form-group">
    <label class="sr-only" for="exampleInputPassword3">Password</label>
    <input type="password" id="httpd_password" name="password" class="form-control" placeholder="Password">
  </div>
  <div class="checkbox">
  </div>
	<input type="submit" class="btn btn-default" id="login" name="login" value="Login"/><br/>
</form>
~;
	#print $form;
	#print "</form>\n";
    }
    print "<br/>\n";

}
	print $footer;
	print $base_cgi->end_html; 
}

displayInputForm();	
 
