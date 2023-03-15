$(document).ready(function() {
    // Hide settings fields by default
    $('div[id^="div_id_settings"]').hide();

    // Check if it's category/project update and show corresponding fields
    if ($('#object-type').text() == 'Update Project') {
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
    }
    if ($('#object-type').text() == 'Update Category') {
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
