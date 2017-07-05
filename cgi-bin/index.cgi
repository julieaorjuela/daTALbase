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


########################################################################
# queries
########################################################################
my $particule_public = " and public != 'No' ";
my $particule_public2 = " where public != 'No'";
if ($user_access){
	$particule_public = "";
	$particule_public2 = "";
}
my $query = "select distinct abrev_spc_bacteria from bacteria b, TALS t where t.bacteria_strain_concate=b.strain_concate $particule_public;";
my $sth = $database_handle->prepare($query);
$sth->execute();
my @bact_species;
while(my @row = $sth->fetchrow_array)
{
	my $bactspecies = $row[0];
	push(@bact_species,$bactspecies);
}

$query = "select distinct bacteria_strain_concate from TALS $particule_public2;";
$sth = $database_handle->prepare($query);
$sth->execute();
my @strains;
while(my @row = $sth->fetchrow_array)
{
        my $strain = $row[0];
        push(@strains,$strain);
}


$query = "select distinct Origin_country from TALS t,bacteria b where t.bacteria_strain_concate=b.strain_concate $particule_public;";
$sth = $database_handle->prepare($query);
$sth->execute();
my @countries;
while(my @row = $sth->fetchrow_array)
{
        my $country = $row[0];
        push(@countries,$country);
}

$query = "select distinct genus from host;";
$sth = $database_handle->prepare($query);
$sth->execute();
my @genus;
while(my @row = $sth->fetchrow_array)
{
	my $genre = $row[0];
	push(@genus,$genre);
}

$query = "select host_code,Specie,Cultivar,genus from host;";
$sth = $database_handle->prepare($query);
$sth->execute();
my %hosts;
while(my @row = $sth->fetchrow_array)
{
	my $host_code = $row[0];
	my $specie = $row[1];
	my $cultivar = $row[2];
	my $genus = $row[3];
	my $host = $genus."_".$specie;
	if ($cultivar ne '-'){
        	$host = $genus."_".$row[1]."_".$row[2];
	}
	$hosts{$host}=$host_code;
}

$query = "select distinct rnaseq_condition_condition_code1,rnaseq_condition_condition_code2 from GeneExpDiffData;";
$sth = $database_handle->prepare($query);
$sth->execute();
my @comparisons;
while(my @row = $sth->fetchrow_array)
{
	my $cond1 = $row[0];
	my $cond2 = $row[1];
	my $comparison = "$cond1 versus $cond2";
	push(@comparisons,$comparison);
}

$query = "select distinct dataset_source from snp_info;";
$sth = $database_handle->prepare($query);
$sth->execute();
my @datasets;
while(my @row = $sth->fetchrow_array)
{
        my $dataset = $row[0];
        push(@datasets,$dataset);
}

$query ="select count(*),bacteria_strain_concate from TALS $particule_public2 group by bacteria_strain_concate;";
$sth = $database_handle->prepare($query);
$sth->execute();
my %repartition;
while(my @row = $sth->fetchrow_array)
{
        my $count = $row[0];
        my $strain = $row[1];
        $repartition{$strain} = $count;
}


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
my $SCRIPT_NAME = "index.cgi";


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
	my $logpart;
        if ($user_access){
                $logpart = qq~<a href="./login2.cgi?logout=yes" style="color: hotpink;">Logout</a>~;
        }
        else{
                $logpart = qq~<a href="./login2.cgi" style="color: hotpink;">Login</a>~;
        }
	
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
<div align="right">$logpart</div>
<div id='tabs'>
<ul>
   <li><a href="#tals">TAL effectors</a></li>
   <li><a href='#targets'>TAL targets in plants (EBEs)</a></li>
   <!--<li><a href='#genes'>Genes</a></li>-->
   <li><a href='#orthologs'>Orthologs</a></li> 
   <li><a href='#experiments'>RNA-Seq/microarray</a></li>
   <li><a href='#snps'>SNPs/indels</a></li>
   <li><a href='#mygenes'>My gene lists</a></li>
   <li></li>
</ul>
~;
	print $tab;

	##########################################################################
	# TALs
	##########################################################################
	#print "<iframe src='$Configuration::CGI_WEB_DIR/chrom_viewer.cgi?session=$session' width='1100' height='500' style='border:solid 0px black;'></iframe><br/><br/>";
	my $tals_example = "TalC\nHD-HD-NN-NN-NG-HA-HD-NE\nTBv1_481\n";


	open(F,">$execution_dir/repartition_tals.txt");
	my %parents_count;
	my %hash_parent;
	foreach my $strain(keys(%repartition)){
		my $count = $repartition{$strain};
		my $parent = "Xoo";
		if ($strain =~/Xoc/){
			$parent = "Xoc";
		}
		$parents_count{$parent}+=$count;
		$hash_parent{$parent}.= "	$strain:$count";
	}
	foreach my $parent(keys(%parents_count)){
		my $gcount = $parents_count{$parent};
		print F "$parent	$gcount".$hash_parent{$parent}."\n";
	}
	close(F);



	if ($tals){$tals_example = $tals;}
	print "<div id='tals'><br/><br/>";
	print "<form name=\"form\">";
	print "<dt>Input</dt>";
	print "<table><tr><td valign=center>Enter a list of TALs:<br/>(RVD sequence, identifiers...)<br/></td><td><textarea rows=\"8\" cols=\"40\" name='tals'>$tals_example</textarea></td></tr>";
	print "<tr><td><dt>Filters</dt></td></tr>";
	print "<tr><td valign=center>Bacteria species (".scalar @bact_species.") </td><td><select multiple name=bacteria id=bacteria size=4 onchange=\"update_strains();\">\n";
	foreach my $bact(@bact_species){
		$bact =~s/ /_/g;
		print "<option>$bact</option>\n";
	}
	print "</select></td></tr>\n";

	print "<tr><td valign=center>Origin Countries (".scalar @countries.")  </td><td><span id='countries_select'><select multiple id=country name=country size=8 onchange=\"update_strains_by_geo();\">\n";
        foreach my $country(@countries){
                print "<option>$country</option>\n";
        }
        print "</select></span></td></tr>\n";

	print "<tr><td valign=center>Strains (".scalar @strains.") </td><td><span id='strains_select'><select multiple id=strain name=strain size=10>\n";
        foreach my $strain(@strains){
                print "<option>$strain</option>\n";
        }
        print "</select></span></td></tr></table>\n";

	print "<input type='hidden' name='session' value='$session'>";
        print "<br/><br/><input type='button' class='submit' value='Search' onclick=\"getTals();\"/>";
	print "</form><br/>";
	print "<span id='results_tals'></span>";
	print "</div>";

	########################################################################
	# EBEs
	########################################################################
	print "<div id='targets'>";
	print "<form name=\"form_tal\">";
	print "<dt>Input</dt>";
	if (!$tals && $genes){$tals=$genes;}	
	print "<table><tr><td valign=center>Enter a list of TALs or genes:</td><td><textarea rows=\"8\" cols=\"20\" name='tals_or_genes'>$tals</textarea></td>";
	print "<tr><td><dt>Filters</dt></td></tr>";
	print "<br/><br/><tr><td>In plant species (".scalar keys(%hosts).")</td><td><select multiple name=hosts id=hosts size=10>\n";
        foreach my $host(keys(%hosts)){
		my $host_code = $hosts{$host};
		print "<option value='$host_code'>$host</option>\n";
	}
        print "</select></td></tr>";
	print "<br/><br/><tr><td>Maximum rank of prediction</td><td><input type=txt name='rank' value=10 size=4>\n";
        print "</td></tr>";
	print "</table>\n";
	print "<input type='hidden' name='session' value='$session'>";
	print "<br/><br/><input type='button' class='submit' value='Search' onclick=\"getEBEs();\"/>";
	print "</form><br/>";
	print "<span id='results_EBE'></span>";
	print "</div>";
	

	#####################################################################
	# Genes
	#####################################################################
	#print "<div id='genes'>";
	#print "<form name=\"form_genes\"><br/><br/>";
	#print "<table><tr><td valign=center>Hosts (".scalar keys(%hosts).")</td><td><select name=hosts>\n";
        #foreach my $host(keys(%hosts)){
	#	my $host_code = $hosts{$host};
        #        print "<option value='$host_code'>$host</option>\n";
        #}
        #print "</select></td></tr></table>\n";
	#print "<br/><br/><input type='button' class='submit' value='Search' onclick=\"getGenes();\"/>";
	#print "</form><br/>";
	#print "<span id='results_genes'></span>";
	#print "</div>";


	####################################################################
	# Orthologs
	####################################################################
	print "<div id='orthologs'>";
	print "<form name=\"form_orthologs\"><br/><br/>";
	print "<dt>Input</dt>";
	print "<br/>Enter a gene name to search for its orthologs: <input name='gene' type='text' value='LOC_Os10g34340'>";
	print "<br/><dt>Filters</dt>";
	print "<br/><table><tr><td valign=center>In plant species (".scalar keys(%hosts).")</td><td><select multiple name=hosts id=hosts size=10>\n";
	foreach my $host(keys(%hosts)){
		my $host_code = $hosts{$host};
		print "<option value='$host_code'>$host</option>\n";
	}
	print "</select></td></tr></table>\n";
	print "<input type='hidden' name='session' value='$session'>";
	print "<br/><br/><input type='button' class='submit' value='Search' onclick=\"getOrthologs();\"/>";
        print "</form><br/>";
        print "<span id='results_orthologs'></span>";
        print "</div>";


	#####################################################################
	# Experiments
	#####################################################################
	print "<div id='experiments'>";

	print "<form name=\"form_experiments\"><br/><br/>";
	print "<dt>Input</dt>";
	print "<table><tr><td valign=center>Enter a list of genes:<i>(ex:LOC_Os01g01160)</i></td><td><textarea rows='8' cols='20' name='genes'>$genes</textarea></td></tr>";
	print "<tr><td><dt>Filters</dt></td></tr>";
	print "<br/><tr><td valign=center>Select a comparison of treatments (".scalar @comparisons.")</td><td><select multiple name=treatments id=treatments size=10>\n";
	my $j = 0;
        foreach my $comparison(@comparisons){
		$j++;
                print "<option value='$comparison'>$comparison</option>\n";
        }
        print "</select></td></tr></table>\n";
	print "<input type='hidden' name='session' value='$session'>";
	print "<br/><br/><input type='button' class='submit' value='Search' onclick=\"getDiffExp();\"/>";
	print "</form><br/>";
	print "<span id='results_experiments'></span>";
	print "</div>";



	##################################################################
	# SNPs
	##################################################################
	print "<div id='snps'>";
	print "<form name=\"form_snps\"><br/><br/>";
        print "<dt>Input</dt>";
	
        print "<br/><table><tr><td valign=center>Select variants dataset:</td><td><select name='variant_dataset'>";
	my $j = 0;
        foreach my $dataset(@datasets){
                $j++;
                print "<option value='$dataset'>$dataset</option>\n";
        }
	print "</select></td></tr>";
	print "<tr><td>Enter a list of genes to search for variants in promoter:<i>(ex:LOC_Os12g40390)</i></td><td><textarea rows='8' cols='20' name='genes'>$genes</textarea></td></tr></table>";
	print "<input type='hidden' name='session' value='$session'>";
	print "<br/><br/><input type='button' class='submit' value='Search' onclick=\"getSNPs();\"/>";
        print "</form><br/>";
        print "<span id='results_snps'></span>";
	print "</div>";


	##################################################################
	# My gene lists
	##################################################################	
	print "<div id='mygenes'>";
	if ($genes_from_EBEs){
                open(O,">$Configuration::HOME_DIR/jvenn/$session.genes_from_EBEs.txt");
                print O $genes_from_EBEs;
                close(O);
        }
        else{
                if (-e "$Configuration::HOME_DIR/jvenn/$session.genes_from_EBEs.txt"){
                        $genes_from_EBEs = `cat $Configuration::HOME_DIR/jvenn/$session.genes_from_EBEs.txt`;
                }
        }
	if ($genes_from_microarray){
                open(O,">$Configuration::HOME_DIR/jvenn/$session.genes_from_microarray.txt");
                print O $genes_from_microarray;
                close(O);
        }
        else{
                if (-e "$Configuration::HOME_DIR/jvenn/$session.genes_from_microarray.txt"){
                        $genes_from_microarray = `cat $Configuration::HOME_DIR/jvenn/$session.genes_from_microarray.txt`;
                }
        }
	my $list1=$genes_from_EBEs;
	my $list2=$genes_from_microarray;
	my $list3="";
	my $list4="";
	my $list5="";
	my $list6="";
	open(O,">$Configuration::HOME_DIR/jvenn/session.$session.html");
        open(F,"$Configuration::HOME_DIR/jvenn/example.html");
        while(<F>){
                if (/list1_to_be_replaced/){
                        $_=~s/list1_to_be_replaced/$list1/g;
                }
                if (/list2_to_be_replaced/){
                        $_=~s/list2_to_be_replaced/$list2/g;
                }
                if (/list3_to_be_replaced/){
                        $_=~s/list3_to_be_replaced/$list3/g;
                }
                if (/list4_to_be_replaced/){
                        $_=~s/list4_to_be_replaced/$list4/g;
                }
                if (/list5_to_be_replaced/){
                        $_=~s/list5_to_be_replaced/$list5/g;
                }
                if (/list6_to_be_replaced/){
                        $_=~s/list6_to_be_replaced/$list6/g;
                }
                print O $_;
        }
        close(F);
        close(O);
	print "<iframe src='$Configuration::WEB_DIR/jvenn/session.$session.html' width='1300' height='600' style=\"border:solid 0px black;\"></iframe><br/><br/>";
	print "</div>";

	print "</div>";
	
	print $footer;
	print $base_cgi->end_html; 
}

displayInputForm();	
 
