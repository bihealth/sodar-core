$(document).ready(function() {
    // Hide settings fields by default
    $('div[id^="div_id_settings"]').hide();

    // Show settings fields if editing a project
    if ($('#object-type').text() == 'Update Project')
        $('div[id^="div_id_settings"]').show();

    // Show settings fields if selected type is project
    $('#div_id_type .form-control').change(function() {
        if ($('#div_id_type .form-control').val() == 'PROJECT')
            $('div[id^="div_id_settings"]').show();
        else
            $('div[id^="div_id_settings"]').hide();
    });
})
