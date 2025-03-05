// static/admin/js/calendar_rules.js
django.jQuery(function($) {
    function updateFieldVisibility() {
        var recurrenceType = $('#id_recurrence_type').val();
        var specificDateRow = $('.field-specific_date').parent('div').parent('div');
        var dayOfWeekRow = $('.field-day_of_week').parent('div').parent('div');
        
        if (recurrenceType === 'specific_date') {
            specificDateRow.show();
            dayOfWeekRow.hide();
            $('#id_day_of_week').val('');
        } else {
            specificDateRow.hide();
            dayOfWeekRow.show();
            $('#id_specific_date').val('');
        }
    }
    
    $('#id_recurrence_type').change(updateFieldVisibility);
    updateFieldVisibility();
});