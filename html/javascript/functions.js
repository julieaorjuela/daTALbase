/**
*******************************************************************************
* functions.js
***************
Version: 0.1
Date:    28/10/2010
Author:  Alexis Dereeper
Contains various helper functions.

*******************************************************************************
*/


/**
*******************************************************************************
* Variables
************
*/


/**
*******************************************************************************
* Functions
************
*/

//var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";

function success_update(transport)
{
  var ajax_div = document.getElementById('results');
  ajax_div.innerHTML = transport.responseText;
}

function failure_update(transport)
{
  var thediv = document.getElementById('results');
  thediv.innerHTML = "Well...it failed !!" ;  
}


function update_strains()
{
	var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
        var params = "action=updateStrains";
	var ajax_div = document.getElementById('strains_select');
	if (document.forms.form.bacteria.options){
                var list = document.forms.form.bacteria.options;
                var list_bacteria="";
                for (var i = list.length - 1; i>=0; i--)
                {
                        if (document.getElementById('bacteria').options[i].selected==true){
                                list_bacteria += list[i].value + ",";
                        }
                }
                params = params + '&bacteria_species=' + list_bacteria;
        }
	url = url + "?" + params;
        $.get( url, function( data ) {
                ajax_div.innerHTML = data;
        });
}

function update_strains_by_geo()
{
        var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
        var params = "action=updateStrainsByGeo";
        var ajax_div = document.getElementById('strains_select');
        if (document.forms.form.country.options){
                var list = document.forms.form.country.options;
                var list_country="";
                for (var i = list.length - 1; i>=0; i--)
                {
                        if (document.getElementById('country').options[i].selected==true){
                                list_country += list[i].value + ",";
                        }
                }
                params = params + '&bacteria_countries=' + list_country;
        }
        url = url + "?" + params;
        $.get( url, function( data ) {
                ajax_div.innerHTML = data;
        });
}

function getTals()
{
	var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
	var params = "action=getTals";
	var ajax_div = document.getElementById('results_tals');
	if (document.forms.form.strain.options){
		var list = document.forms.form.strain.options;
		var list_strains="";
		for (var i = list.length - 1; i>=0; i--)
                {
			if (document.getElementById('strain').options[i].selected==true){
                    list_strains += list[i].value + ",";}
                }
		params = params + '&strain=' + list_strains;
	}
	if (document.forms.form.bacteria.options){
		var list = document.forms.form.bacteria.options;
		var list_bacteria="";
		for (var i = list.length - 1; i>=0; i--)
		{
			if (document.getElementById('bacteria').options[i].selected==true){
				list_bacteria += list[i].value + ",";
			}
		}
		params = params + '&bacteria_species=' + list_bacteria;
	}
	if (document.forms.form.country.options){
                var list = document.forms.form.country.options;
                var list_country="";
                for (var i = list.length - 1; i>=0; i--)
                {
                        if (document.getElementById('country').options[i].selected==true){
                                list_country += list[i].value + ",";
                        }
                }
                params = params + '&country=' + list_country;
        }
	if (String(params).length > 1500){
                alert("Too many entries to proceed");return;
        }
	var res = document.forms.form.tals.value.replace(/\n/g,"~");
	params = params + '&session=' + document.forms.form_tal.session.value; 
	params = params + '&tals=' + res;
	ajax_div.innerHTML = "<i>Querying the database...Please wait...</i>";	
	url = url + "?" + params;
	$.get( url, function( data ) {
		ajax_div.innerHTML = data;
	});
}


function getEBEs()
{
	var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
        var params = "action=getEBEs";
        var ajax_div = document.getElementById('results_EBE');
        if (document.forms.form_tal.tals_or_genes){
		var list_simplified = document.forms.form_tal.tals_or_genes.value.replace(/\n/g,"~");
		var list_simplified2 = list_simplified.replace(/TBv1_/g,"");
                //params = params + '&tals_or_genes=' + document.forms.form_tal.tals_or_genes.value.replace(/\n/g,"~");
                params = params + '&tals_or_genes=' + list_simplified2;
        }
	if (document.forms.form_tal.rank){
                params = params + '&rank=' + document.forms.form_tal.rank.value;
        }
	params = params + '&session=' + document.forms.form_tal.session.value;
	if (document.forms.form_tal.hosts.options){
                var list = document.forms.form_tal.hosts.options;
                var list_hosts="";
                for (var i = list.length - 1; i>=0; i--)
                {
                        if (document.getElementById('hosts').options[i].selected==true){
                    list_hosts += list[i].value + ",";}
                }
                params = params + '&hosts=' + list_hosts;
        }
	if (String(params).length > 1500){
                alert("Too many entries to proceed");return;
        }

        url = url + "?" + params;
	ajax_div.innerHTML = "<i>Querying the database...Please wait...</i>";
	//ajax_div.update("&nbsp;&nbsp;&nbsp;&nbsp;<i>Querying the database...Please wait...</i>\n");
	//var myAjax = new Ajax.Request(url,{method:'post',postBody:params,onLoading:loading_unselected_genes,onSuccess:success_unselected_genes,onFailure:failure_unselected_genes});
        $.get( url, function( data ) {
                ajax_div.innerHTML = data;
        });
}

function getGenes()
{
        var params = "action=getGenes";
        var ajax_div = document.getElementById('results_genes');
        if (document.forms.form_genes.hosts){
                params = params + '&hosts=' + document.forms.form_genes.hosts.value;
        }
        url = url + "?" + params;
        $.get( url, function( data ) {
                ajax_div.innerHTML = data;
        });
}


function getOrthologs()
{
	var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
        var params = "action=getOrthologs";
        var ajax_div = document.getElementById('results_orthologs');
        if (document.forms.form_orthologs.gene){
                params = params + '&gene=' + document.forms.form_orthologs.gene.value;
        }
	if (document.forms.form_orthologs.hosts.options){
                var list = document.forms.form_orthologs.hosts.options;
                var list_hosts="";
                for (var i = list.length - 1; i>=0; i--)
                {
                        if (document.getElementById('hosts').options[i].selected==true){
                    list_hosts += list[i].value + ",";}
                }
                params = params + '&hosts=' + list_hosts;
        }
	params = params + '&session=' + document.forms.form_tal.session.value;
        url = url + "?" + params;
	ajax_div.innerHTML = "<i>Querying the database...Please wait...</i>";
        $.get( url, function( data ) {
                ajax_div.innerHTML = data;
        });
}

function getDiffExp()
{
	var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
	var params = "action=getDiffExp";
	var ajax_div = document.getElementById('results_experiments');
	if (document.forms.form_experiments.genes){
                params = params + '&genes=' + document.forms.form_experiments.genes.value.replace(/\n/g,"~");
        }
	if (String(params).length > 1500){
                alert("Too many genes to proceed");return;
        }
	if (document.forms.form_experiments.treatments){
		var list = document.forms.form_experiments.treatments.options;
		var list_exp ="";
		for (var i = list.length - 1; i>=0; i--)
		{
			if (document.getElementById('treatments').options[i].selected==true){
				list_exp += list[i].value + ",";
			}
		}
                params = params + '&treatments=' + list_exp;
        }
	params = params + '&session=' + document.forms.form_tal.session.value;
	url = url + "?" + params;
	ajax_div.innerHTML = "<i>Querying the database...Please wait...</i>";
	$.get( url, function( data ) {
		ajax_div.innerHTML = data;
	});
}

function getSNPs()
{
	var url = "http://bioinfo-web.mpl.ird.fr/cgi-bin2/datalbase/display_ajax.cgi";
	var params = "action=getSNPs";
	var ajax_div = document.getElementById('results_snps');
	if (document.forms.form_snps.genes){
                params = params + '&genes=' + document.forms.form_snps.genes.value.replace(/\n/g,"~");
        }
	if (String(params).length > 1500){
                alert("Too many genes to proceed");return;
        }
	if (document.forms.form_snps.variant_dataset){
                params = params + '&variant_dataset=' + document.forms.form_snps.variant_dataset.value;
        }
	params = params + '&session=' + document.forms.form_tal.session.value;
	url = url + "?" + params;
	ajax_div.innerHTML = "<i>Querying the database...Please wait...</i>";
        $.get( url, function( data ) {
                ajax_div.innerHTML = data;
        });
}

