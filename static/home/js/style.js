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
$('.tooltipped').tooltip({delay: 50, tooltip: '<text_indent><multiplied_amount>highlighted amounts</multiplied_amount> will be multiplied</text_indent>', html: true});
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