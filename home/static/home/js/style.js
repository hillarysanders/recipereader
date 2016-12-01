$(document).ready(
function(){
    $(".button-collapse").sideNav();
}
);

$(document).ready(function(){
// the "href" attribute of .modal-trigger must specify the modal ID that wants to be triggered
$('.modal-trigger').leanModal();
});


$(document).ready(function(){
$('#servings_tooltip').tooltip({delay: 50, tooltip:
    '<div class="ing_or_dir"><text_indent><multiplied_amount>highlighted amounts</multiplied_amount> will be adjusted</text_indent></div>',
    html: true});
});


function upload_img(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();

        reader.onload = function (e) {
            $('#img_id').attr('src', e.target.result);
        }

        reader.readAsDataURL(input.files[0]);
    }
}

//
//function change_units(kind) {
//  $.getJSON("/change_units/", { pk:{{ recipe.pk }}, change_units: kind }, function(json){
//    alert("Was successful?: " + json['success']);
//  });
//}
//function addClickHandlers() {
//  $("#change_units_metric").click( function() { change_units("metric") });
//  $("#change_units_us").click( function() { change_units("us") });
//  $("#change_units_original").click( function() { change_units("original") });
//}
//$(document).ready(addClickHandlers);