WebPortal = function(){
        var layout;
        return {
            init : function(){
				
				layout = new Ext.BorderLayout('container', {   
					center: {
    	                alwaysShowTabs:true,
        	            tabPosition:'top'
            	    }
                });

				var index = layout.add('center', new Ext.ContentPanel('index', {
	                title:'My Index', 
	                fitToFrame:true,
	                autoScroll:true,
	                autoCreate:true
	            }));
            	var indexBody = index.getEl();

				var tpl = new Ext.Template(
	        		'<div id="{name}"><a href="#">{name}</a></div>'
	        	);
               
              	// initialize the View		
	        	var view = new Ext.JsonView(indexBody, tpl, {
	        		multiSelect: true,
	        		jsonRoot: 'workflows',
	        		emptyText : '<div style="padding:10px;">No workflows available</div>'
	        	});
	        	
	        	view.on('click', function(view, workflow) {
	        		alert('clicked on: ' + workflow)
	        		}, this);
	        	
	        	view.load({url: '/webportal/workflows/', text: 'Loading workflow list...'})
           }
     };
       
}();

Ext.EventManager.onDocumentReady(WebPortal.init, WebPortal, true);
