$(document).ready(function() {
    // Hide settings fields by default
    $('div[id^="div_id_settings"]').hide();

    function showOrHideFields(elements) {
        $('div[id^="div_id_settings"]').each(function () {
            var $parentDiv = $(this);
            if (elements.filter(function() { return $parentDiv.find(this).length }).length > 0) {
                $parentDiv.show();
            } else {
                $parentDiv.hide();
            }
        });
    }

    // Check if it's category/project update and show corresponding fields
    if ($('#object-type').text() == 'Update Project') {
        var projectElements = $([
            'select[data-project-types="project"]',
            'input[data-project-types="project"]',
            'textarea[data-project-types="project"]',
            'select[data-project-types="project,category"]',
            'input[data-project-types="project,category"]',
            'textarea[data-project-types="project,category"]'
        ].join(', '));
        showOrHideFields(projectElements);
    } else if ($('#object-type').text() == 'Update Category') {
        var categoryElements = $([
            'select[data-project-types="category"]',
            'input[data-project-types="category"]',
            'textarea[data-project-types="category"]',
            'select[data-project-types="project,category"]',
            'input[data-project-types="project,category"]',
            'textarea[data-project-types="project,category"]'
        ].join(', '));
        showOrHideFields(categoryElements);
    }

    // Show settings fields if selected type is project/category in update form
    $('#div_id_type .form-control').change(function() {
        var selectedType = $('#div_id_type .form-control').val();
        if (selectedType == 'PROJECT') {
            showOrHideFields(projectElements);
        } else if (selectedType == 'CATEGORY') {
            showOrHideFields(categoryElements);
        }
    });
})
