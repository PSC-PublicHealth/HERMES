<div id='tabs-12'>

<body>	
<h2>{{_('This tests the buttontriple widget')}}</h2>
<div id="putthetriplehere"></div>
<script>
$(function () {
	function altFunc(evt) {
		$(this).parent().buttontriple('set','onEdit',function(e){alert('hit new onEdit');});
	}
	
	$('#putthetriplehere').hrmWidget({
		widget:'buttontriple',
		onEdit:function(evt){ alert('hit onEdit'); },
		//onInfo:function(evt){ alert('hit onInfo'); },
		onDel:function(evt){ 
			console.log('hit onDel'); 
			var $bT = $(this).parent();
			$bT.buttontriple('set','onEdit',null);
			$bT.buttontriple('set','onDel',altFunc);
			console.log('all done');
		},
	});
});
</script>

</body>

</div>