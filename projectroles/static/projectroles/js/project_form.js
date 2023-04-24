$(document).ready(function() {
    // Hide settings fields by default
    $('div[id^="div_id_settings"]').hide();

    // Temporary solution for hiding the public_guest_access field
    $('#div_id_public_guest_access').hide();

    // Check if it's category/project update and show corresponding fields
    if ($('#sodar-pr-project-form-title').attr('data-project-type') === 'PROJECT') {
        $('div[id^="div_id_settings"]').each(function () {
            var $parentDiv = $(this);
            var $projectElements = $parentDiv.find('select[data-project-types="project"]')
                .add($parentDiv.find('input[data-project-types="project"]'))
                .add($parentDiv.find('textarea[data-project-types="project"]'))
                .add($parentDiv.find('select[data-project-types="project,category"]'))
                .add($parentDiv.find('input[data-project-types="project,category"]'))
                .add($parentDiv.find('textarea[data-project-types="project,category"]'));
            if ($projectElements.length > 0) {
                $parentDiv.show();
            } else {
                $parentDiv.hide();
            }
        });

        // Temporary solution for hiding the public_guest_access field
        $('#div_id_public_guest_access').show();
    }

    if ($('#sodar-pr-project-form-title').attr('data-project-type') === 'CATEGORY') {
        $('div[id^="div_id_settings"]').each(function () {
            var $parentDiv = $(this);
            var $categoryElements = $parentDiv.find('select[data-project-types="category"]')
                .add($parentDiv.find('input[data-project-types="category"]'))
                .add($parentDiv.find('textarea[data-project-types="category"]'))
                .add($parentDiv.find('select[data-project-types="project,category"]'))
                .add($parentDiv.find('input[data-project-types="project,category"]'))
                .add($parentDiv.find('textarea[data-project-types="project,category"]'));
            if ($categoryElements.length > 0) {
                $parentDiv.show();
            } else {
                $parentDiv.hide();
            }
        });
    }

    // Show settings fields if selected type is project/category in update form
    $('#div_id_type .form-control').change(function() {
        if ($('#div_id_type .form-control').val() == 'PROJECT') {
            $('div[id^="div_id_settings"]').each(function () {
                var $parentDiv = $(this);
                var $projectElements = $parentDiv.find('select[data-project-types="project"]')
                    .add($parentDiv.find('input[data-project-types="project"]'))
                    .add($parentDiv.find('textarea[data-project-types="project"]'))
                    .add($parentDiv.find('select[data-project-types="project,category"]'))
                    .add($parentDiv.find('input[data-project-types="project,category"]'))
                    .add($parentDiv.find('textarea[data-project-types="project,category"]'));
                if ($projectElements.length > 0) {
                    $parentDiv.show();
                } else {
                    $parentDiv.hide();
                }

                // Temporary solution for hiding the public_guest_access field
                $('#div_id_public_guest_access').show();
            });
        } else if ($('#div_id_type .form-control').val() == 'CATEGORY') {
            $('div[id^="div_id_settings"]').each(function () {
                var $parentDiv = $(this);
                var $categoryElements = $parentDiv.find('select[data-project-types="category"]')
                    .add($parentDiv.find('input[data-project-types="category"]'))
                    .add($parentDiv.find('textarea[data-project-types="category"]'))
                    .add($parentDiv.find('select[data-project-types="project,category"]'))
                    .add($parentDiv.find('input[data-project-types="project,category"]'))
                    .add($parentDiv.find('textarea[data-project-types="project,category"]'));
                if ($categoryElements.length > 0) {
                    $parentDiv.show();
                } else {
                    $parentDiv.hide();
                }
            });
        }
    });
})
