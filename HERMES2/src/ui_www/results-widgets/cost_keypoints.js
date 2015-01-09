;(function($){
	function moneyFormatter(cellValue, options, rowObject) {
		if (cellValue) {
			if (cellValue.formatMoney)
				return cellValue.formatMoney();
			else
				return cellValue			
		}
		else
			return (0.0).formatMoney()
	}
	$.widget("results_widgets.keypoints",{
		options:{
			resultsId:-1,
			modelId:-1,
			scrollable:false,
			resizable:true,
			trant:{
				title:"Cost Key Points"
			}
		},
		
		hideMinor:function(){
			this.containerID = $(this.element).attr('id');
			console.log("Cont: "+this.containerID);
			//$("#"+this.containerID).jqGrid('hideCol',["percooler",'perfreezer','dosespervial']);
		},
		showMinor:function(){
			this.containerID = $(this.element).attr('id');
			console.log("Cont: "+this.containerID);
			//$("#"+this.containerID).jqGrid('showCol',["percooler",'perfreezer','dosespervial']);
		},
		_create:function(){
			trant = this.option.trant;

			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			
			var resultsId = this.options.resultsId;
			var modelId = this.options.modelId;
			
			var chartData = this.options.jsonData;
			
			$.getJSON('json/costs-summary-keypoints',
				{
					modelId:modelId,
					resultsId:resultsId
				})
			.done(function(data) {
				console.log(data);
				if (data.success) {
					$outerTable = $('#'+containerID);
					var $row1 = $(document.createElement('tr'));
					$outerTable.append($row1);
					var $r1c1 = $(document.createElement('td')).addClass('ui-widget-header');
					$row1.append($r1c1);
					$r1c1.text(data.mainTitle);
					if (data.labels.length == data.values.length && data.labels.length == data.fmts.length) {
						for (var i=0; i<data.labels.length; i++) {
							var lbl = data.labels[i];
							var val = data.values[i];
							if (data.fmts[i] == 'money') val = val.formatMoney();
							$row1.append('<td><table><tr><th class="rs_kp_label">'+lbl+'</th></tr><tr><td class="rs_kp_value">'+val+'</td></tr></table></td>');
						}
					}
					else {
						console.log('Error in cost_keypoints: array lengths do not match');
					}
				}
				else {
					alert('{{_("Failed: ")}}'+data.msg);
				}
			})
		.fail(function(jqxhr, textStatus, error) {
				alert('{{_("Error: ")}}'+jqxhr.responseText);
			});
		}
	});
})(jQuery);
	

			
			