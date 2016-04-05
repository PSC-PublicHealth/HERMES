/*
###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
*/
;(function($){

    $.widget("results_widgets.results_summary_page",{
        options:{
            modelId:'',
		    resultsId:'',
		    showCosts:false,
		    randMon:'',
		    rootPath:'',
		    scrollable:true,
		    resizable:false,
		    trant:{
		        title:"Summary of Results"
		    }
        },

    shrink:function(){
        //$("#"+this.vaccGridContainerID).vsgrid("hideMinor");
        $("#"+this.vaccAvailContainerID).vachart("shrink");
        $("#"+this.storeUtilContainerID).suchart("shrink");
        $("#"+this.transUtilContainerID).tuchart("shrink");
    },

    grow:function(){
        //$("#"+this.vaccGridContainerID).vsgrid("showMinor");
        $("#"+this.vaccAvailContainerID).vachart("grow");
        $("#"+this.storeUtilContainerID).suchart("grow");
        $("#"+this.transUtilContainerID).tuchart("grow");
    },

    _create:function(){
        trant = this.options.trant;

        var modelId = this.options.modelId;
        var resultsId = this.options.resultsId;
        var rootPath = this.options.rootPath;
        var showCosts = this.options.showCosts;

        this.containerID = $(this.element).attr('id');
        var containerID = this.containerID;
        this.vaccGridContainerID  = this.containerID + "_vac_grid" + this.options.randMon;
        this.costGridContainerID  = this.containerID + "_cost_grid" + this.options.randMon;
        this.keypointsContainerID = this.containerID + "_keypoints" + this.options.randMon;
        this.vaccAvailContainerID = this.containerID + "_va_chart" + this.options.randMon;
        this.storeUtilContainerID = this.containerID + "_su_chart" + this.options.randMon;
        this.transUtilContainerID = this.containerID + "_tu_chart" + this.options.randMon;

        this.buttonContainerID          = this.containerID + "_buttons" + this.options.randMon;
        this.geobuttonContainerID       = this.containerID + "_geo_button" + this.options.randMon;
        this.netbuttonContainerID       = this.containerID + "_net_button" + this.options.randMon;
        this.xlsbuttonContainerID       = this.containerID + "_xls_button" + this.options.randMon;
        this.xlsDialogContainerID       = this.containerID + "_xls_dialog" + this.options.randMon;
        this.modelInfobuttonContainerID = this.containerID + "_mifo_button" + this.options.randMon;
        this.modelInfoDialogContainerID = this.containerID + "_mifo_dialog" + this.options.randMon;

        var vaccAvailContainerID   = this.vaccAvailContainerID;
        var storeUtilContainerID   = this.storeUtilContainerID;
        var transUtilContainerID   = this.transUtilContainerID;
        var geobuttonContainerID   = this.geobuttonContainerID;
        var netbuttonContainerID   = this.netbuttonContainerID;
        var xlsbuttonContainerID   = this.xlsbuttonContainerID;
        var xlsDialogContainerID   = this.xlsDialogContainerID;
        var mInfobuttonContainerID = this.modelInfobuttonContainerID;
        var mInfoDialogContainerID = this.modelInfoDialogContainerID


        // Add a div for the vaccine grid
        $("#"+this.containerID).append("<table id = '"+ this.vaccGridContainerID + 
        "' class='rs_vaccGrid'></table>");
        //            $("#"+this.containerID).append("<div id='"+ this.buttonContainerID + 
        //                                            "' class='rs_buttons'></div>");

        if(this.options.showCosts){
	        $("#"+this.containerID).append("<table id = '"+ this.costGridContainerID + "' class='rs_costGrid'></table>");
	        $("#"+this.containerID).append("<table id = '"+ this.keypointsContainerID + "' class='rs_keypoints'></table>");
        }
        else{
        	$("#"+this.containerID).append("<div id = 'noCostDiv' style='padding:5px;font-size:12px;'></div>");
        }
        
        $("#"+this.containerID).append("<div id='"+this.containerID+"_buttons' style='width:100%;'></div>");
        $("#"+this.containerID).append("<div id='"+this.containerID+"_buttons' style='width:100%;'></div>");
        $("#"+this.containerID + "_buttons").append("<div id='"+this.geobuttonContainerID+"' class='rs_button'></div>");
        $("#"+this.containerID + "_buttons").append("<div id='"+this.netbuttonContainerID+"' class='rs_button'></div>");
        $("#"+this.containerID + "_buttons").append("<div id='"+this.xlsbuttonContainerID+"' class='rs_button'></div>");
        $("#"+this.containerID + "_buttons").append("<div id='"+ mInfobuttonContainerID+"' class='rs_button'></div>");
        $("#"+this.containerID).append("<div id='"+this.vaccAvailContainerID + 
                "' class='rs_chart'></div>");
        $("#"+this.containerID).append("<div id='"+this.storeUtilContainerID + 
                "' class='rs_chart'></div>");
        $("#"+this.containerID).append("<div id='"+this.transUtilContainerID + 
                "' class='rs_chart'></div>");

        $("#"+this.vaccGridContainerID).vsgrid({
            resultsId: this.options.resultsId,
            modelId: this.options.modelId
        });

        if(this.options.showCosts){
	        $("#"+this.costGridContainerID).csgrid({
	            resultsId: this.options.resultsId,
	            modelId: this.options.modelId
	        });
	
	        
	        $("#"+this.keypointsContainerID).keypoints({
	            resultsId: this.options.resultsId,
	            modelId: this.options.modelId
	        });
	    }
        $("#"+geobuttonContainerID).button();
        $("#"+netbuttonContainerID).button();
        $("#"+xlsbuttonContainerID).button();
        $("#"+mInfobuttonContainerID).button();

        var phrases = {0:'Open Geographic Visualization',
            1:'Open Network Visualization',
            2:'Download Excel Results Spreadsheet',
            3:'This button will open a geographic representation of the full results of '+
                'this simulation experiment in a separate browser tab in which users can dive into the location specific data.',
            4:'This button will open the navigatable network visualation of the full results of this simulation experiment in a separate browser tab.',
            5:'This button will download a fully detailed Excel spreadsheet of the simulation experiment results for further analysis.',
            6:'Save Excel Simulation Experiment Results as...',
            7:'Name for Excel Spreadsheet',
            8:'Save',
            9:'Must define a name to give the file.',
            10:'A problem has occured in the creation of the report.',
            11:'Cancel',
            12:'Total Costs By Supply Chain Level',
            13:'Currency',
            14:'Year',
            15:'There are no costing results to display for this run',
            16:'Get Model Summary Information',
            17:'Close'
        };

        // Handle everything that needs to be translated
        translate_phrases(phrases)
            .done(function(tphrases){
                var tp = tphrases.translated_phrases;

                if(!showCosts){
                	$("#noCostDiv").append("<p>"+tp[15]+"</p>");
                }
                
                $.ajax({
                	url:rootPath+"json/does-model-have-coordinates?modelId="+modelId,
                	data:'json',
                	success:function(data){
                		if(!data.success){
                			alert(data.msg);
                		}
                		else{
                			if(data.hascoord){
                				$("#"+geobuttonContainerID).button("option","label",tp[0]);
                                $("#"+geobuttonContainerID).prop("title",tp[3]);
                			}
                			else{
                				$("#"+geobuttonContainerID).hide();
                			}                      			
                		}                		                		
                	}                	
                });
                
                $("#"+netbuttonContainerID).button("option","label",tp[1]);
                $("#"+netbuttonContainerID).prop("title",tp[4]);
                $("#"+xlsbuttonContainerID).button("option","label",tp[2]);
                $("#"+xlsbuttonContainerID).prop("title",tp[5]);
                $("#"+containerID).append("<div id='"+xlsDialogContainerID+"' title='"+tp[6]+"'></div>");
                var downloadNameID = containerID+"_download_xls_saveas_name";
                $("#"+xlsDialogContainerID).append("<table><tr><td>"+tp[7]+"</td><td><input id='"+
                    downloadNameID+"' type='text'></td></tr></table>");

                $("#"+mInfobuttonContainerID).button("option","label",tp[16]);
                $("#"+containerID).append("<div id='"+mInfoDialogContainerID+"' titel='"+tp[16]+"'><div id='mInfoTabDiv'></div></div>");
                
                //$("#"+mInfobuttonContainerID).prop("title")
                $("#"+mInfoDialogContainerID).dialog({
                	autoOpen:false,
                	modal: true,
                	buttons:{
                		'Close':{
                			text:tp[17],
                			click:function(){
                				$(this).dialog("close");
                			}
                		}
                	}
                });
                
                $("#"+xlsDialogContainerID).dialog({
                    autoOpen:false,
                    height: 300,
                    width: 400,
                    modal: true,
                    buttons:{
                        'Save':{
                            text:tp[8],
                    click:function(){

                        if(!$('#'+downloadNameID).val()){
                            alert(tp[9]);
                        }
                        else {
                            var filename = $("#"+downloadNameID).val();
                            $(this).dialog('close');
                            $.ajax({
                                url: rootPath+'json/create-xls-summary-openpyxl',
                                dataType:'json',
                                data:{modelId:modelId,resultsId:resultsId,filename:filename}})
                                .done(function(data){
                                    if (data.success==true){
                                        $.fileDownload(rootPath+'downloadXLS?shortname='+filename) 
                                    .done(function(){})
                                    .fail(function(){alert(tp[10]);});
                                    }
                                    else {
                                        alert(tp[10]+'\n'+ data.msg);
                                    }
                                })
                            .fail( function(data){
                                alert(data.msg);
                            });
                        }
                    }
                        },
                        Cancel:{
                            text:tp[11],
                            click: function(){
                                $(this).dialog("close");
                            }
                        }
                    },
                    open: function (e,ui){
                        $(this).keypress(function(e) {
                            if (e.keyCode == $.ui.keyCode.ENTER){
                                e.preventDefault();
                                $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
                            }
                        });
                    }    
                });

                if(showCosts){
	                // Zoomable Treemap Widget
	                var zoomID = containerID + "_cost_zoomableTreemap";
	                $("#"+containerID).append("<div id='"+zoomID+"' name='" + zoomID + "'></div>");
	                var zoom_treemap = $("#"+zoomID).treemap({
	                    hasChildrenColor: "steelblue",
	                    noChildrenColor: "#ccc",
	                    jsonDataURLBase: "json/results-cost-hierarchical-value",
	                    jsonDataURLParameters: [
	                    "modelId="+modelId,
	                    "resultsId="+resultsId],
	                    minWidth: 768,
	                    minHeight: 775,
	                    resizable: false,
	                    scrollable: true,
	                    trant: {
	                        "title": tp[12], 
	                        "currency_label": tp[13],
	                        "year_label": tp[14]
	                    }
	                });
	
	                // Hierarchical Barchart Widget
	                var heirBarID = containerID + "_cost_heirBarChart";
	                $("#"+containerID).append("<div id='"+heirBarID+"' name='"+heirBarID+"'></div>");
	                $("#"+heirBarID).barchart({
	                    hasChildrenColor: "steelblue",
	                    noChildrenColor: "#ccc",
	                    jsonDataURLBase: "json/results-cost-hierarchical",
	                    jsonDataURLParameters: [
	                    "modelId="+modelId,
	                    "resultsId="+resultsId],
	                    minWidth: 768,
	                    minHeight: 300,
	                    resizable: false,
	                    scrollable: true,
	                    trant: {
	                        "title": tp[12], 
	                        "currency_label": tp[13],
	                        "year_label": tp[14]
	                    }
	
	                });
	           }
            });



        $.ajax({
            url:this.options.rootPath+'json/results-vaccine-by-place-by-size-hist?modelId='+this.options.modelId+
            '&resultsId='+this.options.resultsId,
            dataType:'json',
            success:function(varesult){
                console.log(varesult);
                $('#'+vaccAvailContainerID).vachart({
                    jsonData:varesult,
                    width:225,
                    height:300
                });
            }
        });

        $.ajax({
            url:this.options.rootPath+'json/result-storage-utilization-by-place-by-levelhist?modelId='+this.options.modelId+
            '&resultsId='+this.options.resultsId,
            dataType:'json',
            success:function(suresult){
                $("#"+storeUtilContainerID).suchart({
                    jsonData:suresult,
                width:225,
                height:300
                });
            }
        });

        $.ajax({
            url:this.options.rootPath+'json/result-transport-utilization-by-route-by-level-hist?modelId='+this.options.modelId+
            '&resultsId='+this.options.resultsId,
            dataType:'json',
            success:function(turesult){
                $('#'+transUtilContainerID).tuchart({
                    jsonData:turesult,
                width:225,
                height:300
                });
            }
        });

        $("#"+this.geobuttonContainerID).click(function(){
            window.open(rootPath+"geographic_visualization?modelId="
                +modelId+"&resultsId="+resultsId);
        });

        $("#"+this.netbuttonContainerID).click(function(){
            window.open(rootPath+"network_results_visualization?modelId="
                +modelId+"&resultsId="+resultsId);
        });

        $("#"+this.xlsbuttonContainerID).click(function(){
            $("#"+xlsDialogContainerID).dialog("open");
        });
        
        $("#"+mInfobuttonContainerID).click(function(){
        	$("#mInfoTabDiv").modelInfotabs({
        		modelId:modelId,
        		rootPath:rootPath
        	});
        	$("#"+mInfoDialogContainerID).dialog("open");
        });
    }
    });
})(jQuery);        
