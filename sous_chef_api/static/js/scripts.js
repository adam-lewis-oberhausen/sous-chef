$(document).ready(function(){
    $('#register-email').on('input', function(){
        var email = $(this).val();
        $.ajax({
            url: '/validate-email/', // Change this if necessary to match your URL pattern
            data: {'email': email},
            dataType: 'json',
            success: function(data){
                if (!data.is_valid) {
                    $('#register-email').removeClass('is-valid').addClass('is-invalid');
                    $('#register-email-feedback').text('Invalid email address.');
                } else if (data.is_taken) {
                    $('#register-email').removeClass('is-valid').addClass('is-invalid');
                    $('#register-email-feedback').text('Email address is already taken.');
                } else {
                    $('#register-email').removeClass('is-invalid').addClass('is-valid');
                    $('#register-email-feedback').text('');
                }
            }
        });
    });

    $('#register-password').on('input', function() {
        var password = $(this).val();
        var feedback = '';

        if (password.length < 8) {
            feedback = 'Password must be at least 8 characters.';
        } else if (!/\d/.test(password)) {
            feedback = 'Password must contain at least one digit.';
        } else if (!/[a-zA-Z]/.test(password)) {
            feedback = 'Password must contain at least one letter.';
        } else if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
            feedback = 'Password must contain at least one special character.';
        }

        if (feedback) {
            $('#register-password').removeClass('is-valid').addClass('is-invalid');
            $('#password-feedback').text(feedback);
        } else {
            $('#register-password').removeClass('is-invalid').addClass('is-valid');
            $('#password-feedback').text('');
        }
    });

    $('#confirm-password').on('input', function() {
        var password = $('#register-password').val();
        var confirmPassword = $(this).val();

        if (password !== confirmPassword) {
            $('#confirm-password').removeClass('is-valid').addClass('is-invalid');
            $('#confirm-password-feedback').text('Passwords do not match.');
        } else {
            $('#confirm-password').removeClass('is-invalid').addClass('is-valid');
            $('#confirm-password-feedback').text('');
        }
    });
});