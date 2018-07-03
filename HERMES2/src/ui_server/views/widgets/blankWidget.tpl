/*
*/

;(function($){
	$.widget("typeWidgets.NameOfWidget",{
		options:{
			modelId:'',
			// more widget options go here
			title:'',
			trant:{
				title: "{{_('Route Specification Form')}}"
			}
		},
		_create:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			
			var thisOptions = this.options;
			
		}
	})';
})(jQuery);
