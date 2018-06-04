#!/usr/bin/perl

=pod

=head1 NAME

display_ajax.cgi - displays an html page for ajax.

=head1 SYNOPSIS

=head1 REQUIRES

=head1 DESCRIPTION

Displays an an html page for ajax.

=cut

use strict;

use DBI;
#use lib "..";

use strict;
use CGI;
use CGI::BaseCGIBootstrap;
use Config::Configuration;
use Carp qw (cluck confess croak);
use warnings;
use Error qw(:try);
use File::Copy;
use SessionManagement::SessionManagement;

my $dbname = $Configuration::DATABASE_NAME;
my $host = $Configuration::DATABASE_HOST;
my $login = $Configuration::DATABASE_LOGIN;
my $password = $Configuration::DATABASE_PASSWORD;

my $jbrowse_link = "http://jbrowse.southgreen.fr/index.html?data=oryza_sativa_japonica_v7";
my $database_handle = DBI->connect("DBI:mysql:database=" . $dbname . ";host=" . $host,$login,$password) || print "Database connection failed: $DBI::errstr";

my $session;
#my $cgi = CGI->new();
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


if ($base_cgi -> param('session') =~/(\d+)/)
{
        $session = $1;
}
if (!$session){
        $session = int(rand(10000000000000));
}
my $execution_dir = $Configuration::EXECUTION_DIR."/".$session;

if (!-d $execution_dir){
	mkdir($execution_dir);
}
my $action = $base_cgi -> param('action');
my $bacteria_species    = $base_cgi -> param('bacteria_species');
my $bacteria_countries    = $base_cgi -> param('bacteria_countries');
my $strain = $base_cgi -> param('strain');
my $tals = $base_cgi -> param('tals');
my $hosts = $base_cgi -> param('hosts');
my $gene = $base_cgi -> param('gene');
my $genes = $base_cgi -> param('genes');
my $treatments = $base_cgi -> param('treatments');
my $tals_or_genes = $base_cgi -> param('tals_or_genes');
my $country = $base_cgi -> param('country');
my $rank = 10;
my $variant_dataset = $base_cgi -> param('variant_dataset');
if ($base_cgi -> param('rank') =~/(\d+)/){
	$rank = $1;
}

my $particule_public = " and public != 'No' ";
my $particule_public2 = " where public != 'No'";
if ($user_access){
        $particule_public = "";
        $particule_public2 = "";
}
if ($action eq "updateStrains"){
	my @bactspec = split(",",$bacteria_species);
	my @strains;
	foreach my $sp(@bactspec){
		$sp =~s/_/ /g;
		my $query = "select distinct bacteria_strain_concate from TALS t, bacteria b where b.strain_concate=t.bacteria_strain_concate and abrev_spc_bacteria='$sp' $particule_public;";
		my $sth = $database_handle->prepare($query);
		$sth->execute();
		while(my @row = $sth->fetchrow_array)
		{
			my $strain = $row[0];
			push(@strains,$strain);
		}
	}
	print "<select multiple id=strain name=strain size=10>";
	foreach my $b(@strains){
		print "<option>$b</option>";
	}
	print "</select>";
	exit;
}
if ($action eq "updateStrainsByGeo"){
        my @bactcountries = split(",",$bacteria_countries);
        my @strains;
        foreach my $sp(@bactcountries){
                $sp =~s/_/ /g;
                my $query = "select distinct bacteria_strain_concate from TALS t, bacteria b where b.strain_concate=t.bacteria_strain_concate and Origin_country='$sp' $particule_public;";
                my $sth = $database_handle->prepare($query);
                $sth->execute();
                while(my @row = $sth->fetchrow_array)
                {
                        my $strain = $row[0];
                        push(@strains,$strain);
                }
        }
        print "<select multiple id=strain name=strain size=10>";
        foreach my $b(@strains){
                print "<option>$b</option>";
        }
        print "</select>";
        exit;
}
########################################################################
## Get TALs
#########################################################################
if ($action eq "getTals"){
	open(my $OUT,">$execution_dir/table.xls");
	print $OUT "Tal key	RVD sequence	gb	Other id	Bacteria	Strain	Origin Country	DisTAL Group\n";
	my $query2 = "select talKEY,RVDseq,gb,OtherID,bacteria_strain_concate,abrev_spc_bacteria,Origin_country,DisTAL_Group,seq from TALS t, bacteria b where t.bacteria_strain_concate=b.strain_concate $particule_public ";
	my $n = 0;
	my $talkeys = "";
	my $talseq = "";
	my $full_talseq = "";
	if ($tals =~/\w+/){
		my @tal_names = split(/~/,$tals);
		my @queries;
		foreach my $tal_name(@tal_names) {
			push(@queries," (talKEY='$tal_name' or RVDseq='$tal_name' or OtherID like '%$tal_name%' or database_long_id like '%$tal_name%')");
		}
		$query2 .= " and (".join("or",@queries) .")";
	}
	if ($strain =~/([\w,]+)/){
		my $strains = $1;
                my @strain_names = split(/,/,$strains);
		my @queries;
		foreach my $st(@strain_names) {
			push(@queries," bacteria_strain_concate='$st' ");
		}
		$query2 .= " and (".join("or",@queries).")";
	}
	if ($country =~/([\.\w,]+)/){
                my $countries = $1;
                my @country_names = split(/,/,$countries);
                my @queries;
                foreach my $co(@country_names) {
                        $co =~s/_/ /g;
                        push(@queries," Origin_country='$co' ");
                }
                $query2 .= " and (".join("or",@queries).")";
        }
	if ($bacteria_species =~/([\.\w,]+)/){
		my $bacterias = $1;
		my @bacteria_names = split(/,/,$bacterias);
		my @queries;
		foreach my $bact(@bacteria_names) {
			$bact =~s/_/ /g;
			push(@queries," abrev_spc_bacteria='$bact' ");
		}
		$query2 .= " and (".join("or",@queries).")";
	}
	my $sth = $database_handle->prepare($query2);
	$sth->execute();
	while(my @row = $sth->fetchrow_array){
		my $talKEY = $row[0];
		my $RVDseq = $row[1];
		my $gb = $row[2];
		my $otherid = $row[3];
		my $strain = $row[4];
		my $bacteria_name = $row[5];
		my $country = $row[6];
		my $group = $row[7];
		my $talsequence = $row[8];
		$n++;
		$talkeys.="$talKEY\n";
		$talseq .=">$talKEY	$RVDseq\n";
		$full_talseq .= ">$talKEY\n$talsequence\n";
		print $OUT "$talKEY	$RVDseq	$gb	$otherid	$bacteria_name	$strain	$country	$group\n";
	}
	close($OUT);
	copy("$execution_dir/table.xls","$Configuration::HOME_DIR/tmp/TALs.$session.xls");
	
	print "<table><tr><td style=\"color:black;font-size: 120%;\"><dt>$n TALs found (<a href=\"$Configuration::WEB_DIR/tmp/TALs.$session.xls\">Excel file</a>)</dt> </td><td><form action='./index.cgi#targets' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='tals' value='$talkeys'><input type='submit' class='submit' value='Search for predicted EBEs'/></input></form></td>";
	print "<td><form action='http://bioinfo-web.mpl.ird.fr/cgi-bin2/talvez/talvez.cgi' method='post' enctype='multipart/form-data' target=_blank><input type=hidden name='tal' value='$talseq'><input type='submit' class='submit' value='Predict EBEs using TALVEZ'/></input></form></td>";
	print "<td><form action='http://bioinfo-web.mpl.ird.fr/cgi-bin2/quetal/quetal.cgi' method='post' enctype='multipart/form-data' target=_blank><input type=hidden name='talseq' value='$full_talseq'><input type='submit' class='submit' value='Phylogeny of TALs using QueTAL'/></input></form></td>";
	print "</tr></table><br/><br/>";
	#print "<form action='./index.cgi#targets' method='post' enctype='multipart/form-data'><input type=hidden name='tals' value='$talkeys'><input type='submit' value='Go to EBEs'></input></form><br><br/>";

}
########################################################################
## Get EBEs
#########################################################################
if ($action eq "getEBEs"){

	open(my $OUT,">$execution_dir/table.xls");
	print $OUT "TAL	rank	score	Chrom	EBE Start	EBE End	EBE sequence	EBE strand	Gene	Annotation	Plant species\n";
	open(my $GFF,">$Configuration::HOME_DIR/tmp/EBE.$session.gff3");
	my $n = 0;
        my $genelist = "";
        my $tallist = "";
        my %tallist_hash;
        my %genelist_hash;

	my %hosts_cor;
	my $query = "select host_code,genus,Specie,Cultivar from host;";
	my $sth = $database_handle->prepare($query);
	$sth->execute();
	while(my @row = $sth->fetchrow_array)
	{
		my $host_code = $row[0];
		my $genus = $row[1];
		my $Specie = $row[2];
		my $Cultivar = $row[3];
		$hosts_cor{$host_code} = "$genus $Specie";
		if ($Cultivar =~/\w+/){
			$hosts_cor{$host_code} = "$genus $Specie $Cultivar";
		}
	}

	my %talnames;
        my $query = "select talKEY,OtherID from TALS;";
        my $sth = $database_handle->prepare($query);
        $sth->execute();
        while(my @row = $sth->fetchrow_array)
        {
                my $talkey = $row[0];
                my $talname = $row[1];
                $talnames{$talkey} = $talname;
        }

	if ($tals_or_genes or $hosts){
		my $talid = $1;
		my @tal_names;
		my $particule;
		my @tal_names = split(/~/,$tals_or_genes);
		foreach my $talname(@tal_names) {
			my $tal_name = $talname;
			my $query = "select start_EBE, stop_EBE, TALBS_sequence, host_gene_Info_GENE_ID,TALS_talKEY,EBEstrand,Rank,SCORE,host_gene_Info_host_host_code,chromosome,gene_annotation from EBEsInPromoters where (TALS_talKEY='".$tal_name."' or host_gene_Info_GENE_ID='$tal_name') and Rank <= $rank;";
				
			my $sth = $database_handle->prepare($query);
			$sth->execute();
			while(my @row = $sth->fetchrow_array)
			{
				my $start = $row[0];
				my $end = $row[1];
				my $talseq = $row[2];
				my $gene = $row[3];
				if ($gene =~/LOC_/){
					$genelist_hash{$gene} = 1;
				}
				my $tal = $row[4];
				my $talname_to_display = $tal;
				if ($talnames{$tal} =~/\w/){
					$talname_to_display = $talnames{$tal};
				}
				#my $plantspecies = $row[5]."_".$row[6]."_".$row[7];
				my $plantspecies = $row[8];
				$tallist_hash{$tal} = 1;
				my $strand = $row[5];$strand=~s/strand//g;
				my $rank = $row[6];
				my $score = $row[7];

				if ($hosts && $hosts !~/$plantspecies/){
					next;
				}
				my $chrom = $row[9];
				my $annotation = $row[10];
				$plantspecies = $hosts_cor{$plantspecies};
				$annotation = substr($annotation,0,20);
				$n++;
				if ($gene =~/LOC_Os(\d+)g/){
					#$chrom = "chr".$1;
					print $GFF "$chrom	EBEs	DNA	$start	$end	.	$strand	.	Name=$talname_to_display;Target=$gene\n";
					my $chrjbrowse = $chrom;
					$chrjbrowse =~s/Chr/chr/g;
					if ($chrjbrowse =~/chr(\d)$/){
						$chrjbrowse = "chr0".$1;
					}
					
					my $link_jbrowse = $jbrowse_link."&loc=$chrom:$start..$end&highlight=$chrjbrowse:$start..$end&tracks=MSUGeneModels%2CEBEs%2CHDRA_SNPs_EBEs%2C3k_indels_EBEs%2C3k_SNPs_EBEs";
					print $OUT "<a href=$link_jbrowse target=_blank>$talname_to_display</a>	$rank	$score	$chrom	$start	$end	$talseq	$strand	$gene	$annotation	$plantspecies\n";
				}
				else{
					print $OUT "$talname_to_display	$rank	$score	$chrom	$start	$end	$talseq	$strand	$gene	$annotation	$plantspecies\n";
				}
			}
		}
		$genelist = join("\n",keys(%genelist_hash));
		$tallist = join("\n",keys(%tallist_hash));
	}
	close($OUT);
	close($GFF);
	$genelist = join("\n",keys(%genelist_hash));
	$tallist = join("\n",keys(%tallist_hash));
	print "<table><tr><td style=\"color:black;font-size: 120%;\"><dt>$n EBEs found (<a href=\"$Configuration::WEB_DIR/tmp/EBE.$session.gff3\">GFF file</a>) </dt></td>";
	print "<td><form action='./index.cgi#experiments' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='genes' value='$genelist'><input type='submit' class='submit' value='RNASeq experiments for these genes'/></input></form></td>";
	print "<td><form action='./index.cgi#tals' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='tals' value='$tallist'><input type='submit' class='submit' value='More info about these TALs'/></input></form></td>";
	print "<td><form action='./index.cgi#snps' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='genes' value='$genelist'><input type='submit' class='submit' value='Get SNPs in promoters in these genes'/></input></form></td>";
	print "<td><form action='./index.cgi#mygenes' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='genes_from_EBEs' value='$genelist'><input type='submit' class='submit' value='Save this list of genes'/></input></form></td>";
	print "</tr></table><br/><br/>";
}
########################################################################
## Get genes
#########################################################################
if ($action eq "getGenes"){
	open(my $OUT,">$execution_dir/table.xls");
	print $OUT "Gene name	Chromosome	Strand	Start	End\n";
	my $query = "select GENE_ID,chromosome,strand,start,end,annotation from host_gene_Info limit 1200;";
	if ($hosts =~/(\w+)/){
		$query = "select GENE_ID,chromosome,strand,start,end,annotation from host_gene_Info where host_host_code='$hosts';";
		my $sth = $database_handle->prepare($query);
		$sth->execute();
		while(my @row = $sth->fetchrow_array){
			my $gene = $row[0];
			my $chrom = $row[1];
			my $strand = $row[2];
			my $start = $row[3];
			my $end = $row[4];
			my $annotation = $row[5];
			print $OUT "$gene	$chrom	$strand	$start	$end\n";
		}
	}
	else{
		my $sth = $database_handle->prepare($query);
		$sth->execute();
		while(my @row = $sth->fetchrow_array){
			my $gene = $row[0];
			my $chrom = $row[1];
			my $strand = $row[2];
			my $start = $row[3];
			my $end = $row[4];
			my $annotation = $row[5];
			print $OUT "$gene	$chrom	$strand	$start	$end\n";
		}
	}
	close($OUT);
}
########################################################################
## Get orthologs
#########################################################################
if ($action eq "getOrthologs"){
	open(my $OUT,">$execution_dir/table.xls");
	print $OUT "Orthologs	Plant species\n";
	my $n = 0;
	my $genelist = "";
	my %genelist_hash;
	if ($gene =~/([\w:\.]+)/){
		$gene = $1;
		my $query = "select Group_ortho from Ortholog_groups where host_gene_Info_GENE_ID='$gene';"; 
		my $sth = $database_handle->prepare($query);
                $sth->execute();
		my @row = $sth->fetchrow_array;
		my $orthogp = $row[0];
		if ($hosts){
			my @host_names = split(/,/,$hosts);
	                foreach my $hostname(@host_names) {
				$query = "select host_gene_Info_GENE_ID,host_gene_Info_host_host_code,genus,Specie,Cultivar from Ortholog_groups o,host h where o.host_gene_Info_host_host_code=h.host_code and Group_ortho='$orthogp' and o.host_gene_Info_host_host_code='$hostname';";
				$sth = $database_handle->prepare($query);
				$sth->execute();
				while(my @row = $sth->fetchrow_array){
					my $ortholog = $row[0];
					$n++;
					my $host = $row[1];
					my $genus = $row[2];
					my $species = $row[3];
					my $cultivar = $row[4];
					$host = $genus."_".$species;
					my $query_annotation = "select annotation from host_gene_Info where GENE_ID='$ortholog';";
					my $sth2 = $database_handle->prepare($query_annotation);
					$sth2->execute();
					my @row_annotation = $sth2->fetchrow_array;
					my $annotation = $row_annotation[0];
					
					if ($cultivar ne '-'){$host.="_".$cultivar;}
					print $OUT "$ortholog	$host\n";
					$genelist_hash{$ortholog} = 1;
				}
			}
		}
		else{
			$query = "select host_gene_Info_GENE_ID,host_gene_Info_host_host_code,genus,Specie,Cultivar from Ortholog_groups o,host h where o.host_gene_Info_host_host_code=h.host_code and Group_ortho='$orthogp';";
			$sth = $database_handle->prepare($query);
			$sth->execute();
			while(my @row = $sth->fetchrow_array){
				my $ortholog = $row[0];
				$n++;
				my $host = $row[1];
				my $genus = $row[2];
				my $species = $row[3];
				my $cultivar = $row[4];
				$host = $genus."_".$species;
				if ($cultivar ne '-'){$host.="_".$cultivar;}
				print $OUT "$ortholog	$host\n";
				$genelist_hash{$ortholog} = 1;
			}
		}
		$genelist = join("\n",keys(%genelist_hash));
	}
	close($OUT);

	copy("$execution_dir/table.xls","$Configuration::HOME_DIR/tmp/orthologs.$session.xls");
	
	print "<table><tr><td style=\"color:black;font-size: 120%;\"><dt>$n orthologs found</b> (<a href=\"$Configuration::WEB_DIR/tmp/orthologs.$session.xls\">Excel file</a>)</dt></td>";
        print "<td><form action='./index.cgi#targets' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='genes' value='$genelist'><input type='submit' class='submit' value='Get EBEs for these genes'/></input></form></td>";
        print "</tr></table><br/><br/>";
}
########################################################################
# Get SNPs
########################################################################
if ($action eq "getSNPs"){
        open(my $OUT,">$execution_dir/table.xls");
        print $OUT "Chromosome	Position	Gene	Variation	Homozygotes for mutation	Heterozygotes for mutation\n";
        my $n = 0;
	my %genelist_hash;
	my %tallist_hash;
        if ($genes){
                my @gene_names = split(/~/,$genes);
		my %hash_snps;
		my %hash_snps2;
		my %hash_snps3;
		my $grep_ind = `grep '#CHROM' SNPs/individuals.$variant_dataset.txt`;
		my @individus_names = split(/\t/,$grep_ind);
                foreach my $genename(@gene_names) {
			my $talid = "";
			my $query = "select chr,position,variation,type,homozygotes_for_mutation,heterozygotes_for_mutation from snp_info where gene='$genename' and dataset_source='$variant_dataset';";
			my $sth = $database_handle->prepare($query);
                        $sth->execute();
                        while(my @row = $sth->fetchrow_array){
				my $chr = $row[0];
				my $pos = $row[1];
				my $variation = $row[2];
				my $ind_list = $row[3];
				my $ind_list2 = $row[4];
				$genelist_hash{$genename} = 1;
				$hash_snps{"$chr-$pos-$genename-$variation"}.= $talid.",";
				$hash_snps2{"$chr-$pos-$genename-$variation"}=$ind_list;
				$hash_snps3{"$chr-$pos-$genename-$variation"}=$ind_list2;
			}
		}
		$n=0;
		
		foreach my $snp(keys(%hash_snps)){
			my ($chr,$pos,$genename,$variation) = split(/-/,$snp);
			
			my $talids = $hash_snps{$snp};
			my $list_ind = $hash_snps2{$snp};
			my $list_ind2 = $hash_snps3{$snp};
			my $nb_inds = scalar(split(",",$list_ind));
			my $nb_inds2 = scalar(split(",",$list_ind2));
			$list_ind = substr($list_ind,0,100);
			$list_ind2 = substr($list_ind2,0,100);
			my $start = $pos-10;
			my $end = $pos+10;
			my $chrom = "chr".$chr;
			my $chrjbrowse = $chrom;
			$chrjbrowse =~s/Chr/chr/g;
			if ($chrjbrowse =~/chr(\d)$/){
				$chrjbrowse = "chr0".$1;
			}
			my $link_jbrowse = $jbrowse_link."&loc=$chr:$start..$end&highlight=$chrjbrowse:$pos..$pos&tracks=MSUGeneModels%2CEBEs%2CHDRA_SNPs_EBEs%2C3k_indels_EBEs%2C3k_SNPs_EBEs";
			$n++;
			print $OUT "$chr	<a target=_blank href='$link_jbrowse'>$pos</a>	$genename	$variation	<a title='$list_ind'>$nb_inds</a>	<a title='$list_ind2'>$nb_inds2</a>\n";
		}
	}
	close($OUT);
	my $genelist = join("\n",keys(%genelist_hash));
	my $tallist = join("\n",keys(%tallist_hash));

	copy("$execution_dir/table.xls","$Configuration::HOME_DIR/tmp/snp.$session.xls");

	print "<table><tr><td style=\"color:black;font-size: 120%;\"><dt>$n variants found</b> (<a href=\"$Configuration::WEB_DIR/tmp/snp.$session.xls\">Excel file</a>) </dt></td>";
        print "<td><form action='./index.cgi#targets' method='post' enctype='multipart/form-data'><input type=hidden name='genes' value='$genelist'><input type=hidden name='session' value='$session'><input type='submit' class='submit' value='Get EBEs for these genes'/></input></form></td>";
	print "<td><form action='./index.cgi#tals' method='post' enctype='multipart/form-data'><input type=hidden name='tals' value='$tallist'><input type='submit' class='submit' value='More info about these TALs'/></input></form></td>";
        print "</tr></table><br/><br/>";
}
########################################################################
## Get differential expressions
#########################################################################
if ($action eq "getDiffExp"){

	my %codes;
	my $query_code = "select exp_code,condition_code from rnaseq_condition;";
	my $sth = $database_handle->prepare($query_code);
	$sth->execute();
	while(my @row = $sth->fetchrow_array){
		my $exp_code = $row[0];
		my $condition_code = $row[1];
		$condition_code=~s/\s//g;
		$exp_code=~s/\s//g;
		$codes{$condition_code} = $exp_code;
	}
	open(my $OUT,">$execution_dir/table.xls");
	print $OUT "Gene	value1	value2	log2_foldchange	p-value	Treatment (cond1 versus cond2)	Experiment code\n";
	$treatments=~s/\n//g;
	$treatments=~s/\r//g;
	my $n = 0;
	my %genes_DE;
	my %hash_expression;
	if ($genes){
		my @gene_names = split(/~/,$genes);
		foreach my $genename(@gene_names) {
			#if ($genename !~/LOC_/){next;}
			my $query = "select host_gene_Info_GENE_ID,value1,value2,log2_foldchange,p_value,rnaseq_condition_condition_code1,rnaseq_condition_condition_code2 from GeneExpDiffData where host_gene_Info_GENE_ID='$genename';";
			if ($treatments){
				my @treatment_names = split(",",$treatments);
				foreach my $treatment(@treatment_names){
					my ($cond1,$cond2)= split(/ versus /,$treatment);
					$query = "select host_gene_Info_GENE_ID,value1,value2,log2_foldchange,p_value,rnaseq_condition_condition_code1,rnaseq_condition_condition_code2 from GeneExpDiffData where host_gene_Info_GENE_ID='$genename' and rnaseq_condition_condition_code1='$cond1' and rnaseq_condition_condition_code2='$cond2';";
			
					my $sth = $database_handle->prepare($query);
					$sth->execute();
					while(my @row = $sth->fetchrow_array){	
						my $val1 = $row[1];
						my $val2 = $row[2];
						my $log2foldchange = $row[3];
						my $pvalue = $row[4];
						my $cond1 = $row[5];
						my $cond2 = $row[6];
						if ($pvalue >= 0.05){next;}
						$n++;
						my $exp_code = $codes{$cond1};
						$genes_DE{$genename}++;
						$hash_expression{$genename}{"$cond2 versus $cond1"} = $log2foldchange;
						print $OUT "$genename	$val1	$val2	$log2foldchange	$pvalue	$cond1 versus $cond2	<a href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=$exp_code' target=_blank>$exp_code</a>\n";
					}
				}
			}
			else{
				my $sth = $database_handle->prepare($query);
				$sth->execute();
				while(my @row = $sth->fetchrow_array){
					my $val1 = $row[1];
					my $val2 = $row[2];
					my $log2foldchange = $row[3];
					my $pvalue = $row[4];
					if ($pvalue >= 0.05){next;}
					$n++;
					my $cond1 = $row[5];
					my $cond2 = $row[6];
					my $exp_code = $codes{$cond1};
					$genes_DE{$genename}++;
					$hash_expression{$genename}{"$cond2 versus $cond1"} = $log2foldchange;
					print $OUT "$genename	$val1	$val2	$log2foldchange	$pvalue	$cond1 versus $cond2	<a href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=$exp_code' target=_blank>$exp_code</a>\n";
				}
			}
		}
		close($OUT);
	}
	elsif ($treatments){
		my @treatment_names = split(",",$treatments);
		foreach my $treatment(@treatment_names){
			my ($cond1,$cond2)= split(/ versus /,$treatment);
			if ($cond1 && $cond2){
				my $query = "select host_gene_Info_GENE_ID,value1,value2,log2_foldchange,p_value from GeneExpDiffData where rnaseq_condition_condition_code1='$cond1' and rnaseq_condition_condition_code2='$cond2';";
				my $sth = $database_handle->prepare($query);
				$sth->execute();
				while(my @row = $sth->fetchrow_array){
					my $genename = $row[0];
					my $val1 = $row[1];
					my $val2 = $row[2];
					my $log2foldchange = $row[3];
					my $pvalue = $row[4];
					if ($pvalue >= 0.05){next;}
					$n++;
					my $exp_code = $codes{$cond1};
					$genes_DE{$genename}++;
					$hash_expression{$genename}{"$cond2 versus $cond1"} = $log2foldchange;
					print $OUT "$genename	$val1	$val2	$log2foldchange	$pvalue	$cond1 versus $cond2	<a href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=$exp_code' target=_blank>$exp_code</a>\n";
				}
			}
		}
		close($OUT);	
	}
	else{
		my $query = "select host_gene_Info_GENE_ID,value1,value2,log2_foldchange,p_value,rnaseq_condition_condition_code1,rnaseq_condition_condition_code2 from GeneExpDiffData;";
		my $sth = $database_handle->prepare($query);
		$sth->execute();
		while(my @row = $sth->fetchrow_array){
			my $genename = $row[0];
			my $val1 = $row[1];
			my $val2 = $row[2];
			my $log2foldchange = $row[3];
			my $pvalue = $row[4];
			if ($pvalue >= 0.05){next;}
			$n++;
			my $cond1 = $row[5];
			my $cond2 = $row[6];
			my $exp_code = $codes{$cond1};
			$genes_DE{$genename}++;
			$hash_expression{$genename}{"$cond2 versus $cond1"} = $log2foldchange;
			print $OUT "$genename	$val1	$val2	$log2foldchange	$pvalue	$cond1 versus $cond2	<a href='https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=$exp_code' target=_blank>$exp_code</a>\n";
		}
	}
	my $config_viewer2;
	open(F,">$execution_dir/genes_DE.txt");
	print F "Gene	Nb\n";
	foreach my $gene(sort {$a<=>$b} keys(%genes_DE)){
		open(D,">$execution_dir/$gene.txt");
		print D "Experiment	Log2FC	condition1	condition2\n";
		my $ref_hash = $hash_expression{$gene};
		my %hash2 = %$ref_hash;
		my $ntimes = scalar keys(%hash2);
		foreach my $comp(keys(%hash2)){
			my $log2foldchange = $hash_expression{$gene}{$comp};
			#$comp = substr($comp,0,10);
			$comp =~s/versus/\//g;
			my @conditions = split(" versus ",$comp);
			my $condition1 = $conditions[0];
			my $condition2 = $conditions[1];
			my $val_condition;
			if ($log2foldchange > 0){
				$val_condition = 2**$log2foldchange;
				#print D "$condition1	1\n";
				#print D "$condition2	$val_condition2\n";
			}
			else{
				#$log2foldchange = -$log2foldchange;
				$val_condition = 2**$log2foldchange;
				#print D "$condition2	1\n";
				#print D "$condition1	$val_condition1\n";
			}
			print D "$comp	$log2foldchange	1	$val_condition\n";
		}
		close(D);
		my $num = $genes_DE{$gene};
		print F "$gene	$num\n";

		$config_viewer2 .= qq~
'$gene' =>
        {
                "select_title" => "$gene (differentially expressed $ntimes times)",
                "per_chrom" => "off",
                "title" => "$gene",
                "subtitle" => "differentially expressed $ntimes times",
                "type" => "column",
                "stacking" => "off",
                "yAxis" => "Log2FoldChange",
                "file" => "$execution_dir/$gene.txt",
        },~;

	}
	close(F);

	my $config_viewer .= qq~
'nbgenes' =>
        {
                "select_title" => "Differentially expressed genes",
                "per_chrom" => "off",
                "title" => "Differentially expressed genes",
                "subtitle" => "Identified several times",
                "type" => "column",
                "stacking" => "off",
                "yAxis" => "Nb times",
                "file" => "$execution_dir/genes_DE.txt",
        },~;

	open(my $T,">$execution_dir/$session.chrom_viewer.conf");
	print $T $config_viewer2;
	close($T);

	
	my $genelist = join("\n",keys(%genes_DE));
	print "<iframe src='$Configuration::CGI_WEB_DIR/chrom_viewer.cgi?session=$session' width='1100' height='500' style='border:solid 0px black;'></iframe><br/><br/>";

	copy("$execution_dir/table.xls","$Configuration::HOME_DIR/tmp/DEgenes.$session.xls");

	print "<table><tr><td style=\"color:black;font-size: 120%;\"><dt>". scalar keys(%genes_DE)." differentially expressed genes found ($n entries)</b> (<a href=\"$Configuration::WEB_DIR/tmp/DEgenes.$session.xls\">Excel file</a>) </dt></td>";
        print "<td><form action='./index.cgi#snps' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='genes' value='$genelist'><input type='submit' class='submit' value='Get SNPs in promoters in these genes'/></input></form></td>";
	print "<td><form action='./index.cgi#mygenes' method='post' enctype='multipart/form-data'><input type=hidden name='session' value='$session'><input type=hidden name='genes_from_microarray' value='$genelist'><input type='submit' class='submit' value='Save this list of genes'/></input></form></td>";
        print "</tr></table><br/><br/>";


}
my $config_table .= qq~
'table'=>
{
	"select_title" => "Results table",
	"file" => "$execution_dir/table.xls",
},~;

open(my $T,">$execution_dir/tables.conf");
print $T $config_table;
close($T);


print "<iframe src='$Configuration::CGI_WEB_DIR/table_viewer.cgi?session=$session' width='1250' height='650' style='border:solid 0px black;'></iframe><br/><br/>";
#print "<form action='./index.cgi#targets' method='post' enctype='multipart/form-data'><input type=hidden name='host_species' value='$bacteria_species'><input type='submit' value='Go to EBEs'></input></form>";


