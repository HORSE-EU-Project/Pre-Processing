/*addCSS("../css/styles.css");

// Include CSS file
function addCSS(filename){
    var head = document.getElementsByTagName('head')[0];
   
    var style = document.createElement('link');
    style.href = filename;
    style.type = 'text/css';
    style.rel = 'stylesheet';
    head.append(style);
   }
*/
var FormStuff = {
  
    init: function() {
      this.applyConditionalRequired();
      this.bindUIActions();
    },
    
    bindUIActions: function() {
      $("input[type='radio'], input[type='checkbox']").on("change", this.applyConditionalRequired);
    },
    
    applyConditionalRequired: function() {
      
      $(".require-if-active").each(function() {
        var el = $(this);
        if ($(el.data("require-pair")).is(":checked")) {
          el.prop("required", true);
        } else {
          el.prop("required", false);
        }
      });
      
    }
    
  };
  
  FormStuff.init();