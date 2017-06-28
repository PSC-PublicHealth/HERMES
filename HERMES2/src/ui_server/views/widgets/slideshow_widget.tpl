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
			nextFunctions:[],
			backFunctions:[],
			doneFunction:function(){},
			doneURL:'{{rootPath}}models-top?crmb=clear',
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
							 .addClass('slide_button_active').button("option","disabled",false); //show();
		},
		deactivateButton: function(name){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var ButtonId = thisContainerId + "_" + name;
			$("#" + thisContainerId).data(name + "Active",false);
			$("#" + ButtonId).removeClass('slide_button_active')
			 				 .addClass('slide_button_deact').button("option","disabled",true);//"hide();
		},
		hideButton: function(name){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var ButtonId = thisContainerId + "_" + name;
			$("#" + thisContainerId).data(name + "Active",false);
			$("#" + ButtonId).removeClass('slide_button_active')
			 				 .addClass('slide_button_deact').hide();
		},
		showButton: function(name){ 
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var ButtonId = thisContainerId + "_"+name;
			$("#" + thisContainerId).data(name + "Active",true);
			$("#" + ButtonId).removeClass('slide_button_deact')
							 .addClass('slide_button_active').show();
		},
		currentSlide: function(){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			
			return $("#"+ thisContainerId).data('activeSlide');
		},
		hideSlide: function(slideNumber){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var slideShowDiv = thisContainerId + "_slideShow";
			
			var currentActiveSlide = $("#"+thisContainerId).data('activeSlide');
			var numSlides = $("#"+thisContainerId).data('numberSlides');
			var activeSlideOffsets = $("#" + thisContainerId).data('slideOffsets');
			
			// Cannot hide the current slide
			if (slideNumber == currentActiveSlide){
				alert("slideShowWithFlowControl trying to hide the currently active slide is an invalid operation");
				return false;
			}
			// Validate the slide number passed to the function
			if(slideNumber < 0 || slideNumber > numSlides-1){
				alert("slideShowWithFlowControl: calling hideSlide with an invalid slide number");
				return false;
			}
			
			//current slide already hidden
			if(activeSlideOffsets[slideNumber] == -1){
				return true;
			}
			var slideToHide = $("."+thisContainerId + "_slide_" + slideNumber);
			slideToHide.hide();
			
			//update Active offsets
			
			activeSlideOffsets[slideNumber] = -1;
			for (i=slideNumber+1; i<numSlides;++i){
				if (activeSlideOffsets[i] > -1){
					activeSlideOffsets[i]--;
				}
			}
			$("#"+thisContainerId).data('slideOffsets',activeSlideOffsets);
			console.log("Hide new active offsets = ");
			console.log(activeSlideOffsets);
			return true;
		},
		showSlide: function(slideNumber){
			this.containerId = $(this.element).attr('id');
			var $this = this;
			var thisContainerId = this.containerId;
			var slideShowDiv = thisContainerId + "_slideShow";
			
			var currentActiveSlide = $("#"+thisContainerId).data('activeSlide');
			var numSlides = $("#"+thisContainerId).data('numberSlides');
			var activeSlideOffsets = $("#" + thisContainerId).data('slideOffsets');
			
			// Validate the slide number passed to the function
			if(slideNumber < 0 || slideNumber > numSlides-1){
				alert("slideShowWithFlowControl: calling hideSlide with an invalid slide number");
				return false;
			}
			
			//current slide already visible
			if(activeSlideOffsets[slideNumber]>-1){
				return true;
			}
			
			var slideToShow = $("."+thisContainerId + "_slide_" + slideNumber);
			
			slideToShow.show();
			
			//update Active Offsets
			
			var maxOffset = -1;
			var slideCount = slideNumber-1;
			while(maxOffset == -1 && slideCount > -1){
				maxOffset = activeSlideOffsets[slideCount]
				slideCount --;
			}
			//console.log("maxOffset = " + maxOffset);
			
			activeSlideOffsets[slideNumber] = maxOffset + 1;
			
			for(var i = slideNumber+1;i<numSlides;++i){
				if(activeSlideOffsets[i] != -1){
					activeSlideOffsets[i]++;
				}
			}
			$("#"+thisContainerId).data('slideOffsets',activeSlideOffsets);
			
			console.log("Show new active offsets = " + activeSlideOffsets);
			return true;
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
			var slideOffset = $("#"+thisContainerId).data('slideOffsets');
			var numSlides = $("#"+thisContainerId).data('numberSlides');
			//console.log("Current Before: " + currentActiveSlide + " " + numSlides);
			
			// ok first off find out if this is the last slide available
			
			var moreActiveSlides = false;
			for (var i=currentActiveSlide + 1; i < numSlides; i++){
				if(slideOffset[i] > -1){
					moreActiveSlides = true;
					break;
				}
			}
			
			if(moreActiveSlides){
				//$this.data('activeSlide',currentActiveSlide++);
				currentActiveSlide++; 
				var previousActiveSlide = currentActiveSlide;
				while((currentActiveSlide != numSlides-1) && slideOffset[currentActiveSlide] == -1){
					currentActiveSlide++;
				}
				
				// find out if there are anymore active slides
				var isLastSlide = false;
				for(var i=currentActiveSlide+1;i<numSlides;i++){
					if(slideOffset[i] != -1){
						isLastSlide = true;
						break;
					}
				}
				
				$("#"+slideShowDiv).animate({scrollLeft:slideWidth*slideOffset[currentActiveSlide]},600);
				
				if(!isLastSlide){
					//currentActiveSlide = previousActiveSlide;
					$this.hideButton("next");
					$this.showButton("done");
				}
				$this.activateButton("back");
				console.log("Current Next Setting: " + currentActiveSlide);
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
			var slideOffset = $("#"+thisContainerId).data('slideOffsets');
			
			console.log("Current Before: " + currentActiveSlide + " " + numSlides);
			
			// find out if there are anymore active slides
			var moreActiveSlides = false;
			for (var i=currentActiveSlide-1;i>-1;i--){
				if(slideOffset[i] > -1){
					moreActiveSlides = true;
					break;
				}
			}
			console.log("back more active on slide "+ currentActiveSlide + " is " + moreActiveSlides);
			if(moreActiveSlides){
				//$this.data('activeSlide',currentActiveSlide++);
				currentActiveSlide--;
				while((currentActiveSlide != 0) && slideOffset[currentActiveSlide] == -1){
					currentActiveSlide--;
				}
				$("#"+slideShowDiv).animate({scrollLeft:slideWidth*slideOffset[currentActiveSlide]},600);
				
				var isLastSlide = false;
				for(var i=currentActiveSlide-1;i>-1;i--){
					if(slideOffset[i] != -1){
						isLastSlide = true;
						break;
					}
				}
				if(!isLastSlide){
					$this.deactivateButton("back");
				}
				$this.showButton("next");
				$this.hideButton("done");
				console.log("Current Back Setting: " + currentActiveSlide);
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
			
			var thisOptions = this.options;
			
			
			$("#"+thisContainerId).children("div").addClass("widget_slide");
			$("#"+thisContainerId).append("<div id ='" + slideShowDiv + "' class='widget_main'></div>");
			var slideCount = 0;
			$(".widget_slide").each(function(){
				$("#"+slideShowDiv).append(this);
				$(this).addClass(thisContainerId + "_slide_"+slideCount);
				slideCount++;
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
			
			var backBut = $("#"+backButtonId).button();
			backBut.button("option","disabled",true);//.hide();
			var nextBut = $("#"+nextButtonId).button();
			nextBut.button("option","disabled",true);//.hide();
			var doneBut = $("#"+doneButtonId).button().hide();
			
			$("#"+thisContainerId).data('numberSlides', $("#" + slideShowDiv + " .widget_slide").length);
			$("#"+thisContainerId).data('activeSlide', 0);
			var activeSlideOffsets = {};
			
			//initialize so that we can hide slides
			for (var i=0;i<$("#"+thisContainerId).data('numberSlides');++i){
				activeSlideOffsets[i] = i;
			}
			$("#"+thisContainerId).data('slideOffsets',activeSlideOffsets);
			$("#"+thisContainerId).data('nextActive',false);
			$("#"+thisContainerId).data('backActive',false);
			$("#"+thisContainerId).data('doneActive',false);
			
			// Check validity of next Functions
			if(thisOptions.nextFunctions.length > 0){
				if(thisOptions.nextFunctions.length != $("#"+thisContainerId).data('numberSlides')-1){
					alert("{{_('in slideshowwithflowcontrol widget: next functions is not the right length')}}");
				}
			}
			
			if(thisOptions.backFunctions.length > 0){
				if(thisOptions.backFunctions.length != $("#"+thisContainerId).data('numberSlides')-1){
					alert("{{_('in slideshowwithflowcontrol widget: back functions is not the right length')}}");
				}
			}
			
			
			var nextBut = $("#" + nextButtonId).button();
			var backBut = $("#" + backButtonId).button();
			var doneBut = $("#" + doneButtonId).button();
			
			nextBut.click(function(e){
				e.preventDefault();
				var returnVal = true;
				if(thisOptions.nextFunctions.length>0){
					var activeSlide = $("#"+thisContainerId).data('activeSlide');
					returnVal = thisOptions.nextFunctions[activeSlide]();
				}
				if(returnVal){
					$this.nextSlide();
				}
			});
			
			backBut.click(function(e){
				e.preventDefault();
				var returnVal = true;
				if(thisOptions.backFunctions.length>0){
					var activeSlide = $("#"+thisContainerId).data('activeSlide');
					returnVal = thisOptions.backFunctions[activeSlide-1]();
				}
				if(returnVal){
					$this.backSlide();
				}
			});
			
			doneBut.click(function(e){
				thisOptions.doneFunction();
				window.location=thisOptions.doneUrl;
			});
			
			if(this.options.activateNext){
				this.activateButton("next");
			}
			
		}
	});
})(jQuery);
