(function() {
	// Load plugin specific language pack
	tinymce.PluginManager.requireLangPack('pulog_upload');

	tinymce.create('tinymce.plugins.pulog_upload', {
		/**
		 * Initializes the plugin, this will be executed after the plugin has been created.
		 * This call is done before the editor instance has finished it's initialization so use the onInit event
		 * of the editor instance to intercept that event.
		 *
		 * @param {tinymce.Editor} ed Editor instance that the plugin is initialized in.
		 * @param {string} url Absolute URL to where the plugin is located.
		 */
		init : function(ed, url) {
			// Register the command so that it can be invoked by using tinyMCE.activeEditor.execCommand('mceUpload');
			ed.addCommand('mceUpload', function() {
				ed.windowManager.open({
					file : '/upload/',
					width : 540 + parseInt(ed.getLang('pulog_upload.delta_width', 0)),
					height : 300 + parseInt(ed.getLang('pulog_upload.delta_height', 0)),
					inline : 1
				}, {
					plugin_url : url, // Plugin absolute URL
					post_url : window.location.href.toString().substring(window.location.href.toString().indexOf("/admin")) // get the current post url
				});
			});

			// Register upload button
			ed.addButton('pulog_upload', {
				title : 'pulog_upload.desc',
				cmd : 'mceUpload',
				image : url + '/img/upload.gif'
			});

			// Add a node change handler, selects the button in the UI when a image is selected
			ed.onNodeChange.add(function(ed, cm, n) {
				cm.setActive('pulog_upload', n.nodeName == 'IMG');
			});
		},

		/**
		 * Creates control instances based in the incomming name. This method is normally not
		 * needed since the addButton method of the tinymce.Editor class is a more easy way of adding buttons
		 * but you sometimes need to create more complex controls like listboxes, split buttons etc then this
		 * method can be used to create those.
		 *
		 * @param {String} n Name of the control to create.
		 * @param {tinymce.ControlManager} cm Control manager to use inorder to create new control.
		 * @return {tinymce.ui.Control} New control instance or null if no control was created.
		 */
		createControl : function(n, cm) {
			return null;
		},

		/**
		 * Returns information about the plugin as a name/value array.
		 * The current keys are longname, author, authorurl, infourl and version.
		 *
		 * @return {Object} Name/value array containing information about the plugin.
		 */
		getInfo : function() {
			return {
				longname : 'pulog_upload plugin',
				author : 'pulog project',
				authorurl : 'http://code.google.com/p/pulog/',
				infourl : 'http://code.google.com/p/pulog/',
				version : "1.0"
			};
		}
	});

	// Register plugin
	tinymce.PluginManager.add('pulog_upload', tinymce.plugins.pulog_upload);
})();
