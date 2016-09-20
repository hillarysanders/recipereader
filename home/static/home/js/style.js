$(document).ready(
function(){
    $(".button-collapse").sideNav();
}
);

function popup(e, message){
    if(!confirm(message))e.preventDefault();
}

function promptWindow() {
  // Create template
  var box = document.createElement("div");
  var cancel = document.createElement("button");
  cancel.innerHTML = "Cancel";
  cancel.onclick = function() { document.body.removeChild(this.parentNode) }
  var text = document.createTextNode("Please enter a message!");
  var input = document.createElement("textarea");
  box.appendChild(text);
  box.appendChild(input);
  box.appendChild(cancel);

  // Style box
  box.style.position = "absolute";
  box.style.width = "400px";
  box.style.height = "300px";

  // Center box.
  box.style.left = (window.innerWidth / 2) -100;
  box.style.top = "100px";

  // Append box to body
  document.body.appendChild(box);

}