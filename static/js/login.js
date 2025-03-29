// login.js - Script for login and password recovery

document.addEventListener('DOMContentLoaded', function() {
    // Get login form elements
    const loginForm = document.getElementById('login-form-element');
    const accountTypeSelect = document.getElementById('account-type');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const accountTypeError = document.getElementById('account-type-error');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');
    
    // Get forgot password link
    const forgotPassword = document.getElementById('forgot-password');
    
    // Login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate form
            let isValid = true;
            
            if (!accountTypeSelect.value) {
                accountTypeError.style.display = 'block';
                accountTypeSelect.classList.add('error');
                isValid = false;
            } else {
                accountTypeError.style.display = 'none';
                accountTypeSelect.classList.remove('error');
            }
            
            if (!validateEmail(emailInput.value)) {
                emailError.style.display = 'block';
                emailInput.classList.add('error');
                isValid = false;
            } else {
                emailError.style.display = 'none';
                emailInput.classList.remove('error');
            }
            
            if (!passwordInput.value) {
                passwordError.style.display = 'block';
                passwordInput.classList.add('error');
                isValid = false;
            } else {
                passwordError.style.display = 'none';
                passwordInput.classList.remove('error');
            }
            
            if (isValid) {
                const loginData = {
                    account_type: accountTypeSelect.value,
                    email: emailInput.value,
                    password: passwordInput.value
                };
                
                // Show loading message
                const loginBtn = document.querySelector('#login-btn');
                const originalBtnText = loginBtn.textContent;
                loginBtn.textContent = 'Logging in...';
                loginBtn.disabled = true;
                
                // Make actual API call to login
                fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(loginData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Login successful! Redirecting to dashboard...');
                        // In a real application, redirect to dashboard
                        // window.location.href = '/dashboard';
                    } else {
                        alert('Login failed: ' + data.message);
                        // Reset button
                        loginBtn.textContent = originalBtnText;
                        loginBtn.disabled = false;
                    }
                })
                .catch(error => {
                    alert('An error occurred during login. Please try again.');
                    // Reset button
                    loginBtn.textContent = originalBtnText;
                    loginBtn.disabled = false;
                });
            }
        });
    }
    
    // Forgot password link
    if (forgotPassword) {
        forgotPassword.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('forgotPasswordStep1').style.display = 'block';
        });
    }
    
    // Initialize verification code inputs if present on the page
    const recoveryCodeInputs = document.querySelectorAll('.recovery-code-input');
    if (recoveryCodeInputs.length > 0) {
        setupCodeInputs(recoveryCodeInputs);
    }
    
    // Add direct click handler for verify button
    const verifyButton = document.getElementById('verifyResetTokenBtn');
    if (verifyButton) {
        verifyButton.addEventListener('click', function(e) {
            e.preventDefault();
            submitVerificationCode();
        });
        
        // Ensure button is clickable
        verifyButton.removeAttribute('disabled');
    }

    // Back to Login from forgot password - update to handle both links and buttons
    document.querySelectorAll('.backToLogin').forEach(function(element) {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('login-form').style.display = 'block';
            document.getElementById('forgotPasswordStep1').style.display = 'none';
            document.getElementById('forgotPasswordStep2').style.display = 'none';
            document.getElementById('forgotPasswordStep3').style.display = 'none';
            // Clear any error messages
            if (document.getElementById('forgotPasswordError')) {
                document.getElementById('forgotPasswordError').textContent = '';
            }
            if (document.getElementById('verifyResetTokenError')) {
                document.getElementById('verifyResetTokenError').textContent = '';
            }
            if (document.getElementById('resetPasswordError')) {
                document.getElementById('resetPasswordError').textContent = '';
            }
        });
    });
});

// Function to validate email - for forgot password form
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

// Function to set up verification code inputs
function setupCodeInputs(inputs) {
    if (!inputs || inputs.length === 0) return;
    
    // Clear all inputs first
    inputs.forEach(input => input.value = '');
    inputs[0].focus();
    
    // Make the verify button accessible immediately - remove disabled
    const verifyButton = document.getElementById('verifyResetTokenBtn');
    if (verifyButton) {
        verifyButton.removeAttribute('disabled');
    }
    
    inputs.forEach((input, index) => {
        // Simple input handler - just focus next field
        input.addEventListener('input', function() {
            // Allow only digits and limit to one character
            this.value = this.value.replace(/[^0-9]/g, '').substr(0, 1);
            
            // Move to next field if this one has a value and not the last field
            if (this.value && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
        });
        
        // Handle backspace
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && !this.value && index > 0) {
                inputs[index - 1].focus();
            }
        });
        
        // Select text on focus
        input.addEventListener('focus', function() {
            this.select();
        });
    });
}

// Function to start the resend timer
function startResendTimer(timerElement, buttonElement, countElement, seconds = 60) {
    if (!timerElement || !buttonElement || !countElement) return;
    
    buttonElement.classList.add('disabled');
    timerElement.style.display = 'block';
    countElement.textContent = seconds;
    
    const timer = setInterval(() => {
        seconds--;
        countElement.textContent = seconds;
        
        if (seconds <= 0) {
            clearInterval(timer);
            buttonElement.classList.remove('disabled');
            timerElement.style.display = 'none';
        }
    }, 1000);
    
    return timer;
}

// Submit email for password reset
document.getElementById('forgotPasswordForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('resetEmail').value;
    const userTypeRadios = document.getElementsByName('reset-account-type');
    let accountType = '';
    
    for (const radio of userTypeRadios) {
        if (radio.checked) {
            accountType = radio.value;
            break;
        }
    }
    
    if (!validateEmail(email)) {
        document.getElementById('forgotPasswordError').textContent = 'Please enter a valid email address';
        return;
    }
    
    if (!accountType) {
        document.getElementById('forgotPasswordError').textContent = 'Please select an account type';
        return;
    }
    
    document.getElementById('forgotPasswordError').textContent = '';
    document.getElementById('resetSubmitBtn').disabled = true;
    document.getElementById('resetSubmitBtn').textContent = 'Sending...';
    
    // Send request to server
    fetch('/api/forgot-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            account_type: accountType
        }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('resetSubmitBtn').disabled = false;
        document.getElementById('resetSubmitBtn').textContent = 'Submit';
        
        if (data.success) {
            // Move to step 2 - verification code
            document.getElementById('forgotPasswordStep1').style.display = 'none';
            document.getElementById('forgotPasswordStep2').style.display = 'block';
            document.getElementById('resetEmail2').textContent = email;
            startResendTimer(
                document.getElementById('resendRecoveryTimer'),
                document.getElementById('resendRecoveryCode'),
                document.getElementById('resend-recovery-count')
            );
            const recoveryCodeInputs = document.querySelectorAll('.recovery-code-input');
            setupCodeInputs(recoveryCodeInputs);
            
            // Force check after a delay
            setTimeout(manuallyEnableVerifyButton, 500);
        } else {
            document.getElementById('forgotPasswordError').textContent = data.message || 'An error occurred';
        }
    })
    .catch(error => {
        document.getElementById('resetSubmitBtn').disabled = false;
        document.getElementById('resetSubmitBtn').textContent = 'Submit';
        document.getElementById('forgotPasswordError').textContent = 'Error: ' + error.message;
        console.error('Error:', error);
    });
});

// Verify reset token
document.getElementById('verifyResetTokenForm').addEventListener('submit', function(e) {
    e.preventDefault();
    submitVerificationCode();
});

// Function to submit verification code - extracted to be reusable
function submitVerificationCode() {
    const verifyButton = document.getElementById('verifyResetTokenBtn');
    if (verifyButton) {
        verifyButton.textContent = 'Verifying...';
    }
    
    // Get all digits from inputs
    const codeInputs = document.querySelectorAll('.recovery-code-input');
    let token = '';
    for (const input of codeInputs) {
        token += input.value || '';
    }
    
    // Make sure we have a 6-digit code
    if (token.length !== 6) {
        document.getElementById('verifyResetTokenError').textContent = 'Please enter all 6 digits of the verification code';
        if (verifyButton) {
            verifyButton.textContent = 'Verify';
        }
        return;
    }
    
    // Reset error message
    document.getElementById('verifyResetTokenError').textContent = '';
    
    // Send verification request
    fetch('/api/verify-reset-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: token })
    })
    .then(response => response.json())
    .then(data => {
        if (verifyButton) {
            verifyButton.textContent = 'Verify';
        }
        
        if (data.success) {
            // Move to password reset step
            document.getElementById('forgotPasswordStep2').style.display = 'none';
            document.getElementById('forgotPasswordStep3').style.display = 'block';
        } else {
            document.getElementById('verifyResetTokenError').textContent = data.message || 'Invalid verification code';
        }
    })
    .catch(error => {
        if (verifyButton) {
            verifyButton.textContent = 'Verify';
        }
        document.getElementById('verifyResetTokenError').textContent = 'Error: Could not verify code. Please try again.';
    });
}

// Set new password
document.getElementById('resetPasswordForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmNewPassword').value;
    
    if (newPassword.length < 8) {
        document.getElementById('resetPasswordError').textContent = 'Password must be at least 8 characters';
        return;
    }
    
    if (newPassword !== confirmPassword) {
        document.getElementById('resetPasswordError').textContent = 'Passwords do not match';
        return;
    }
    
    document.getElementById('setNewPasswordBtn').disabled = true;
    document.getElementById('setNewPasswordBtn').textContent = 'Updating...';
    
    // Send request to reset password
    fetch('/api/reset-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_password: newPassword }),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('setNewPasswordBtn').disabled = false;
        document.getElementById('setNewPasswordBtn').textContent = 'Set New Password';
        
        if (data.success) {
            // Show success message and redirect to login
            document.getElementById('forgotPasswordStep3').style.display = 'none';
            document.getElementById('login-form').style.display = 'block';
            
            // Show success message
            const successAlert = document.createElement('div');
            successAlert.className = 'alert alert-success';
            successAlert.textContent = 'Password has been reset successfully. You can now log in with your new password.';
            
            // Insert before login form
            const loginForm = document.getElementById('login-form');
            loginForm.parentNode.insertBefore(successAlert, loginForm);
            
            // Remove the alert after 5 seconds
            setTimeout(() => {
                successAlert.remove();
            }, 5000);
        } else {
            document.getElementById('resetPasswordError').textContent = data.message || 'An error occurred';
        }
    })
    .catch(error => {
        document.getElementById('setNewPasswordBtn').disabled = false;
        document.getElementById('setNewPasswordBtn').textContent = 'Set New Password';
        document.getElementById('resetPasswordError').textContent = 'Error: ' + error.message;
        console.error('Error:', error);
    });
});

// Resend verification code for password reset
document.getElementById('resendRecoveryCode').addEventListener('click', function(e) {
    e.preventDefault();
    if (this.classList.contains('disabled')) return;
    
    const resetEmail = document.getElementById('resetEmail2').textContent;
    if (!resetEmail) {
        document.getElementById('verifyResetTokenError').textContent = 'Email not found. Please try again.';
        return;
    }
    
    this.classList.add('disabled');
    startResendTimer(
        document.getElementById('resendRecoveryTimer'),
        document.getElementById('resendRecoveryCode'),
        document.getElementById('resend-recovery-count')
    );
    
    // Send API request to resend code - this would be an actual API call in production
    // For now, just show a success message
    setTimeout(() => {
        document.getElementById('verifyResetTokenError').textContent = 'Verification code resent. Please check your email.';
    }, 1000);
});

// Add a direct function to manually enable the verify button immediately
function manuallyEnableVerifyButton() {
    const verifyButton = document.getElementById('verifyResetTokenBtn');
    if (verifyButton) {
        verifyButton.removeAttribute('disabled');
    }
}

// Add resend code handler
document.addEventListener('DOMContentLoaded', function() {
    // Existing code...
    
    // Set up resend code button handler
    const resendBtn = document.getElementById('resendRecoveryCode');
    if (resendBtn) {
        resendBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Check if disabled
            if (this.classList.contains('disabled')) {
                return;
            }
            
            // Clear all verification inputs
            const codeInputs = document.querySelectorAll('.recovery-code-input');
            codeInputs.forEach(input => {
                input.value = '';
            });
            
            // Get email from display
            const emailElement = document.getElementById('resetEmail2');
            const email = emailElement ? emailElement.textContent : '';
            
            if (!email) {
                document.getElementById('verifyResetTokenError').textContent = 'Email not found. Please go back and try again.';
                return;
            }
            
            // Clear error message
            document.getElementById('verifyResetTokenError').textContent = '';
            
            // Disable button during request
            this.classList.add('disabled');
            this.textContent = 'Sending...';
            
            // Get account type from session if possible
            // For simplicity, we'll just use 'user' as default
            const accountType = 'user';
            
            // Request a new code
            fetch('/api/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    account_type: accountType
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('New verification code sent');
                    document.getElementById('verifyResetTokenError').textContent = 'New verification code sent. Please check your email.';
                    
                    // Start timer
                    startResendTimer(
                        document.getElementById('resendRecoveryTimer'),
                        document.getElementById('resendRecoveryCode'),
                        document.getElementById('resend-recovery-count')
                    );
                    
                    // Focus first input field
                    if (codeInputs.length > 0) {
                        codeInputs[0].focus();
                    }
                } else {
                    document.getElementById('verifyResetTokenError').textContent = data.message || 'Failed to send new code';
                    this.classList.remove('disabled');
                    this.textContent = 'Resend Code';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('verifyResetTokenError').textContent = 'Error: ' + error.message;
                this.classList.remove('disabled');
                this.textContent = 'Resend Code';
            });
        });
    }
}); 