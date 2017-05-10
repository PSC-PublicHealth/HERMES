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
	$.widget("divWidgets.slideShowWithFlowControl",{
		options:{
			width: 800,
			height: 500,
			activateNext: true,
			trant:{
				title: "{{_('Slide Show Widget')}}"
			}
		},
		activateButton: function(name){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var ButtonId = thisContainerId + "_"+name;
			$("#" + thisContainerId).data(name + "Active",true);
			$("#" + ButtonId).removeClass('slide_button_deact')
							 .addClass('slide_button_active').show();
		},
		deactivateButton: function(name){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var ButtonId = thisContainerId + "_" + name;
			$("#" + thisContainerId).data(name + "Active",false);
			$("#" + ButtonId).removeClass('slide_button_active')
			 				 .addClass('slide_button_deact').hide();
		},
		
		nextSlide: function(){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var slideShowDiv = thisContainerId + "_slideShow";
			var nextButtonId = thisContainerId + "_next";
			var backButtonId = thisContainerId + "_back";
			var doneButtonId = thisContainerId + "_back";
			var slideWidth = $("#"+slideShowDiv).width();
			
			var currentActiveSlide = $("#"+thisContainerId).data('activeSlide');
			var numSlides = $("#"+thisContainerId).data('numberSlides');
			//console.log("Current Before: " + currentActiveSlide + " " + numSlides);
			if(currentActiveSlide != numSlides-1){
				//$this.data('activeSlide',currentActiveSlide++);
				currentActiveSlide++;
				$("#"+slideShowDiv).animate({scrollLeft:slideWidth*currentActiveSlide},600);
				if(currentActiveSlide == numSlides-1){
					$this.deactivateButton("next");
					$this.activateButton("done");
				}
				$this.activateButton("back");
				//console.log("Current After: " + currentActiveSlide);
				$("#"+thisContainerId).data('activeSlide',currentActiveSlide);
			}	
		},
		backSlide: function(){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var slideShowDiv = thisContainerId + "_slideShow";
			var nextButtonId = thisContainerId + "_next";
			var slideWidth = $("#"+slideShowDiv).width();
			
			var currentActiveSlide = $("#"+thisContainerId).data('activeSlide');
			var numSlides = $("#"+thisContainerId).data('numberSlides');
			//console.log("Current Before: " + currentActiveSlide + " " + numSlides);
			if(currentActiveSlide != 0){
				//$this.data('activeSlide',currentActiveSlide++);
				currentActiveSlide--;
				$("#"+slideShowDiv).animate({scrollLeft:slideWidth*currentActiveSlide},600);
				if(currentActiveSlide == 0){
					$this.deactivateButton("back");
				}
				$this.activateButton("next");
				$this.deactivateButton("done");
				//console.log("Current After: " + currentActiveSlide);
				$("#"+thisContainerId).data('activeSlide',currentActiveSlide);
			}	
		},
		_create: function(){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var slideShowDiv = thisContainerId + "_slideShow";
			var buttonContainerID = thisContainerId + "_buttons";
			var nextButtonId = thisContainerId + "_next";
			var backButtonId = thisContainerId + "_back";
			var doneButtonId = thisContainerId + "_done";
			
			
			$("#"+thisContainerId).children("div").addClass("widget_slide");
			$("#"+thisContainerId).append("<div id ='" + slideShowDiv + "' class='widget_main'></div>");
			$(".widget_slide").each(function(){
				$("#"+slideShowDiv).append(this);
			});
			$("#"+thisContainerId).prepend("<div id='" + thisContainerId + "_buttons' class='slideshow_button_cont'>"
					+ "<button id='"+ backButtonId + "' class='slide_button_deact' >{{_('Back')}}</button>"
					+ "<button id='"+ nextButtonId + "' class='slide_button_deact' >{{_('Next')}}</button>"
					+ "<button id='"+ doneButtonId + "' class='slide_button_deact'>{{_('Done')}}</button>"
					+ "</div>");
			
			// set the width and height of slides
			var width = this.options.width;
			var height = this.options.height;
			$(".widget_slide").width(width).height(height);
			$(".widget_main").width(width).height(height);
			// set up starting button conditions
			
			// all buttons are hidden at the beginning
			
			var backBut = $("#"+backButtonId).button().hide();
			var nextBut = $("#"+nextButtonId).button().hide();
			var doneBut = $("#"+doneButtonId).button().hide();
			
			$("#"+thisContainerId).data('numberSlides', $("#" + slideShowDiv + " .widget_slide").length);
			$("#"+thisContainerId).data('activeSlide', 0);
			$("#"+thisContainerId).data('nextActive',false);
			$("#"+thisContainerId).data('backActive',false);
			$("#"+thisContainerId).data('doneActive',false);
			
			var nextBut = $("#" + nextButtonId).button();
			var backBut = $("#" + backButtonId).button();
			var doneBut = $("#" + doneButtonId).button();
			
			nextBut.click(function(e){
				e.preventDefault();
				$this.nextSlide();
			});
			
			backBut.click(function(e){
				e.preventDefault();
				$this.backSlide();
			});
			
			if(this.options.activateNext){
				this.activateButton("next");
			}
			
		}
	});
})(jQuery);
