
$(document).ready(function() {
    /*****************************
     Disable unpack archive widget
     *****************************/
    $('input#id_unpack_archive').attr('disabled', 'disabled');
});

/************************************
 Enable unpack widget if file is .zip
 ************************************/
$('input#id_file').change(function() {
    var fileName = $(this).val();

    // The actual content type is checked upon upload in the form
    if (fileName.substr(fileName.length - 4) === '.zip') {
        $('input#id_unpack_archive').attr('disabled', false);
    }

    else {
        $('input#id_unpack_archive').attr(
            'disabled', 'disabled').prop('checked', false);
    }
});

/*****************
 Manage checkboxes
 *****************/
function checkAll(elem) {
    var checkboxes = document.getElementsByTagName('input');
    if (elem.checked) {
        for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].type === 'checkbox') {
                checkboxes[i].checked = true;
            }
        }
    }

    else {
        for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].type === 'checkbox') {
                checkboxes[i].checked = false;
            }
        }
    }
}
