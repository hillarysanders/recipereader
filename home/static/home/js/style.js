$(document).ready(
function(){
    $(".button-collapse").sideNav();
}
);

function popup(e, message){
    if(!confirm(message))e.preventDefault();
}
