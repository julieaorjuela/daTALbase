#!/usr/bin/perl

use strict;
use warnings;
use Carp qw (cluck confess croak);

use DBI;
use CGI;
use lib "..";

use Config::Configuration;


my $cgi = CGI->new();


my $chromosome = $cgi -> param('chrom');
my $display = $cgi -> param('display');
my $session = $cgi -> param('session');

my $config;
if ($session)
{
	$config = $Configuration::EXECUTION_DIR."/$session/$session.chrom_viewer.conf";
}
else
{
	$config = 'chrom_viewer.conf';
}
my %CONFIG;
eval '%CONFIG = ( ' . `cat $config` . ')';
die "Error while loading configuration file: $@n" if $@;



sub log10 {
my $n = shift;
return log($n)/log(10);
}


my $chrom_to_display;
if ($chromosome)
{
	$chrom_to_display = $chromosome;
}

print $cgi->header();

print $cgi->start_html(
	-title  => "Chromosome viewer",
	-script => {
		'-language' => 'javascript', 
		'-src'		=> "$Configuration::JAVASCRIPT_DIR/jquery-1.5.1.min.js"
    },

);

if (scalar keys(%CONFIG) > 1){
print "Display: <select name='display' id='display' onchange='reload();'>";
foreach my $key(sort keys(%CONFIG))
{
	if (!$display){$display=$key;}
	my $select_title = $CONFIG{$key}{"select_title"};
	if ($display eq $key)
	{
		print "<option value='$key' selected=\"selected\">$select_title</option>\n";
	}
	else
	{
		print "<option value='$key'>$select_title</option>\n";
	}
}
print "</select>\n";
}
else{
	foreach my $key(sort keys(%CONFIG))
	{
        	if (!$display){$display=$key;}
	}
}
print "<input type=\"hidden\" id=\"session\" value=\"$session\"> \n";

my $split_per_chrom = $CONFIG{$display}{"per_chrom"};

my $file = $CONFIG{$display}{"file"};
my $type_display = $CONFIG{$display}{"type"};
my %chroms;
my %headers;
my %data;
my @inds;
my @xaxis;
my $max = 0;
open(my $F,$file) or print "<br><b>Not able to open file $file</b><br/>";
my $numline = 0;
my $n = 0;
my $k_start = 2;
if ($type_display eq 'heatmap'){$k_start = 1;}
if ($type_display eq 'column'){$k_start = 1;}


my $cat_pie;
my $data_pie = "";
if ($type_display eq 'pie')
{	
	my @categories_pie;
	my $nsection = 0;
	while(<$F>)
	{
		my $line = $_;
		chomp($line);
		$line =~s/\n//g;
		$line =~s/\r//g;
		my @values = split(/\t/,$line);
		my $indice = $values[0];
		push(@categories_pie,$indice);
		my $val = $values[1];
		my @nbs;
		my @cat_interne;
		for (my $i = 2; $i <= $#values; $i++)
		{
			my ($type,$n) = split(":",$values[$i]);
			push(@nbs,$n);
			push(@cat_interne,$type);
		}
		my $cat_pie_interne = "'" . join("','",@cat_interne) . "'";
		my $nb_pie_interne = join(",",@nbs);
		$data_pie .= "{y: $val,color: colors[$nsection],drilldown: {name: '$indice',categories: [$cat_pie_interne],data: [$nb_pie_interne],color: colors[$nsection]}},";
		$nsection++;
	}
	$cat_pie = "'" . join("','",@categories_pie) . "'";
}
else
{
	while(<$F>)
	{
		$numline++;
		my $line = $_;
		chomp($line);
		$line =~s/\n//g;
		$line =~s/\r//g;
		my @values = split(/\t/,$line);
		if ($numline == 1)
		{
			for (my $k = $k_start; $k <= $#values; $k++)
			{
				$headers{$k} = $values[$k];
				push(@inds,$headers{$k});
			}
		}
		else
		{
			my $chr = $values[0];
			if (!$chrom_to_display or $CONFIG{$display}{"per_chrom"} eq "off")
			{
				$chrom_to_display=$chr;
				push(@xaxis,$chr);
			}
			my $x = $values[1];
			$chroms{$chr} = 1;
			if ($chr eq $chrom_to_display)
			{		
				for (my $k = $k_start; $k <= $#values; $k++)
				{
					my $y = $values[$k];	
					if ($y > $max){$max = $y;}
					if ($type_display eq 'heatmap')
					{
						my $num = $k - 1;
						my $header = "";
						if ($headers{$k}){$header = $headers{$k};}
						$data{$header}.= "[$n,$num,$y],";
					}
					elsif ($type_display eq 'column')
					{
						$data{$headers{$k}}.= "$y,";
					}
					elsif ($type_display eq 'scatter')
					{
						#$data{$headers{$k}}.= "{name: '$chr',x: $x,y: $y},";
						my $name = $values[1];
						$data{$values[0]}.= "{name: '$name',x: $values[2],y: $values[3]},";
					}
					else
					{
						$data{$headers{$k}}.= "[$x,$y],";
					}
				}
				$n++;
			}
		}
	}
}
close($F);

	 
if ($split_per_chrom eq "on")
{
	print "Chromosome: <select name='chrom' id='chrom' onchange='reload();'>";
	foreach my $chr(sort keys(%chroms))
	{
		if ($chromosome && $chromosome =~/$chr$/)
		{
			print "<option value='$chr' selected=\"selected\">$chr</option>\n";
		}
		else
		{
			print "<option value='$chr'>$chr</option>\n";
		}
	}
	print "</select>\n";
}
else
{
	print "<input type=hidden id='chrom' value=''>";
}

print "<br/><br/>";


my $colors = "[0, '#3060cf'],[0.5, '#fffbbc'],[0.9, '#c4463a'],[1, '#c4463a']";
if ($CONFIG{$display}{"colors"})
{
	$colors = $CONFIG{$display}{"colors"};
}

my $colorAxis = qq~
colorAxis: {
            stops: [
                $colors
            ],
            min: 0,
            max: $max,
            startOnTick: false,
            endOnTick: false,
            labels: {
                format: '{value}.'
            }
        },
~;
my $zoomType = "xy";
my $y_categories = "";
my $x_categories = "";
if ($type_display ne 'heatmap')
{
	$colorAxis = "";
	$zoomType = "x";
}

if ($type_display eq 'heatmap')
{
	$y_categories = "categories: ['" . join("','",@inds) . "'],";
	if (scalar @xaxis)
	{
		$x_categories = "categories: ['" . join("','",@xaxis) . "'],labels: {enabled:true, rotation: 90, align: 'left'},";
	}
}
if ($type_display eq 'column')
{
	if (scalar @xaxis)
	{
		$x_categories = "categories: ['" . join("','",@xaxis) . "'],labels: {enabled:true, rotation: 40, align: 'left'},";
	}
}


my $point_size = 1;
if ($CONFIG{$display}{"point_size"})
{
	$point_size = $CONFIG{$display}{"point_size"};
}


my $javascript = qq~
	
	<script type="text/javascript">
	
	function reload()
	{
		var chrom = document.getElementById('chrom').value;	
		var display = document.getElementById('display').value;	
		var session = document.getElementById('session').value;	
		var url = window.location.href; 
		var base_url = url.split('?');
		url = base_url[0];
		url += '?chrom='+chrom;
		url += '&display='+display;
		url += '&session='+session;
		window.location.href = url;
	}
	
	</script>
~;

print $javascript;



my $html = qq~


<script src="http://code.highcharts.com/highcharts.js"></script>
<script src="http://code.highcharts.com/modules/data.js"></script>
<script src="http://code.highcharts.com/modules/exporting.js"></script>
<script src="http://code.highcharts.com/modules/heatmap.js"></script>



<!-- Additional files for the Highslide popup effect -->
<script type="text/javascript" src="http://highslide.com/highslide/highslide-full.min.js"></script>
<script type="text/javascript" src="http://highslide.com/highslide/highslide.config.js" charset="utf-8"></script>
<link rel="stylesheet" type="text/css" href="http://highslide.com/highslide/highslide.css" />

	<div id='plot' style='min-width: 600px; height: 400px margin: 0 auto'></div>
	~;
print $html;

my $stacking = "";
if ($CONFIG{$display}{"stacking"} eq "normal")
{
	$stacking = "stacking: 'normal',";
}

my $tooltip = "";
my $plotline = "";
if ($type_display eq 'scatter')
{
	$tooltip = "tooltip: {headerFormat: '<b></b>',pointFormat: '<b>{point.name}'},";
	$plotline = "plotLines: [{value: 0,color: 'black',width: 2,}]";
}
my $pointer = "";
if ($CONFIG{$display}{"link"})
{
        my $jbrowse_link = $CONFIG{$display}{"link"};
        $pointer = qq~
	cursor:'pointer',
        point:
        {
                                                events: {
                                                        click: function (e) {
                                                                        x = this.x - 20000;
                                                                        y = this.x + 20000;

                                                                hs.htmlExpand(null, {
                                                                        pageOrigin: {
                                                                                x: e.pageX,
                                                                                y: e.pageY
                                                                        },
                                                                        headingText: 'Links',
                                                                        maincontentText: '<a href=$jbrowse_link&loc=$chrom_to_display:'+x+'..'+y+'&highlight=$chrom_to_display:'+x+'..'+y+' target=_blank>View in JBrowse</a>',


                                    width: 200,
                                height:70
                                });
                            }
                        }
                    },
        ~;
}

my $title = $CONFIG{$display}{"title"};
if ($split_per_chrom eq "on")
{
	$title .= " ($chrom_to_display)";
}
	
#type: '$CONFIG{$display}{"type"}',


if ($type_display eq 'pie')
{
	my $javascript = qq~
	<script type='text/javascript'>
	\$(function () {

	
    var colors = Highcharts.getOptions().colors,
        categories = [$cat_pie],
        data = [$data_pie],
        browserData = [],
        versionsData = [],
        i,
        j,
        dataLen = data.length,
        drillDataLen,
        brightness;


    // Build the data arrays
    for (i = 0; i < dataLen; i += 1) {

        // add browser data
        browserData.push({
            name: categories[i],
            y: data[i].y,
            color: data[i].color
        });

        // add version data
        drillDataLen = data[i].drilldown.data.length;
        for (j = 0; j < drillDataLen; j += 1) {
            brightness = 0.2 - (j / drillDataLen) / 5;
            versionsData.push({
                name: data[i].drilldown.categories[j],
                y: data[i].drilldown.data[j],
                color: Highcharts.Color(data[i].color).brighten(brightness).get()
            });
        }
    }

	var chart;
		
							
	\$(document).ready(function() 
	{
		chart = new Highcharts.Chart({
				
			chart: {
					renderTo: 'plot',
					type: '$CONFIG{$display}{"type"}',
					zoomType: '$zoomType'
				},
	
    
        title: 
		{
			text: '$title'
		},
		subtitle: 
		{
			text: '$CONFIG{$display}{"subtitle"}'
		},
        
        plotOptions: {
            pie: {
                shadow: false,
                center: ['50%', '50%']
            }
        },
        series: [{
            name: 'term',
            data: browserData,
            size: '80%',
            dataLabels: {
                formatter: function () {
                    return this.y >= 1 ? this.point.name : null;
                },
                color: 'white',
                distance: -80
            }
        }, {
            name: 'term',
            data: versionsData,
            size: '80%',
            innerSize: '50%',
            dataLabels: {
                formatter: function () {
                    //display only if larger than 1
                    return this.y > 1 ? '<b>' + this.point.name + ':</b> ' + this.y + ''  : null;
                }
            }
        }]
    });
});
});
</script>
~;
	print $javascript;
}
else
{
	my $javascript = qq~
<script type='text/javascript'>
		\$(function () {
		var chart;
		
							
		\$(document).ready(function() {
			chart = new Highcharts.Chart({
				chart: {
					renderTo: 'plot',
					type: '$CONFIG{$display}{"type"}',
					zoomType: '$zoomType'
				},
				title: 
				{
					text: '$title'
				},
				subtitle: 
				{
					text: '$CONFIG{$display}{"subtitle"}'
				},
				yAxis: {
					$y_categories
					title: {
						text: '$CONFIG{$display}{"yAxis"}'
					},
					$plotline
				},
				xAxis: {
					$x_categories
					title: {
						text: '$CONFIG{$display}{"xAxis"}'
					},
					$plotline
				},
				$colorAxis
				plotOptions: {
 					$CONFIG{$display}{"type"}: {
 						$stacking
						$tooltip
						marker: {
							radius:$point_size,
						}
					}
 				},
				series: [~;
	
print $javascript;
	
foreach my $header(keys(%data))
{
	print "{\n";
	#if ($type_display ne 'scatter')
	#{
		print "name: '$header',turboThreshold:20000,\n";
	#}
	print "data: [" . $data{$header} . "],\n";
	print "marker: {radius:$point_size},\n";
	print "$pointer\n";
	print "},\n";
}
my $javascript_end = qq~			
				]
			});
		});

	});
		
		</script>
~;
print $javascript_end;
}
			






