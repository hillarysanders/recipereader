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

