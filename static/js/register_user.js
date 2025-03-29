// register_user.js - Script for the user registration form

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements - Main registration steps
    const steps = document.querySelectorAll('.step');
    const formSteps = document.querySelectorAll('.form-step');
    const registerBtn = document.getElementById('register-btn');
    const backToForm = document.getElementById('back-to-form');
    const verifyCodeBtn = document.getElementById('verify-code');
    
    // Form inputs and error elements
    const accountTypeSelect = document.getElementById('account-type');
    const companyIdInput = document.getElementById('company-id');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    
    const accountTypeError = document.getElementById('account-type-error');
    const companyIdError = document.getElementById('company-id-error');
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');
    const confirmPasswordError = document.getElementById('confirm-password-error');
    
    // Verification elements
    const resendCodeBtn = document.getElementById('resend-code-btn');
    const resendTimer = document.getElementById('resend-timer');
    const timerCount = document.getElementById('timer-count');
    const verificationInputs = document.querySelectorAll('.verification-code-input');
    
    // Recovery form elements
    const recoverCompanyId = document.getElementById('recover-company-id');
    const cancelRecovery = document.getElementById('cancel-recovery');
    const sendRecoveryEmailBtn = document.getElementById('send-recovery-email');
    const recoveryEmailInput = document.getElementById('recovery-email');
    const recoveryEmailError = document.getElementById('recovery-email-error');
    const backToRecoveryEmail = document.getElementById('back-to-recovery-email');
    const verifyRecoveryCode = document.getElementById('verify-recovery-code');
    const resendRecoveryBtn = document.getElementById('resend-recovery-btn');
    const recoveryResendTimer = document.getElementById('recovery-resend-timer');
    const recoveryTimerCount = document.getElementById('recovery-timer-count');
    const recoveryCodeInputs = document.querySelectorAll('.recovery-code-input');
    
    // Elements for the third recovery step
    const recoveredCompanyIdInput = document.getElementById('recovered-company-id');
    const copyRecoveredIdBtn = document.getElementById('copy-recovered-id');
    const backToLoginBtn = document.getElementById('back-to-login');
    const useForRegistrationBtn = document.getElementById('use-for-registration');
    
    // Initialize buttons as disabled
    if (verifyCodeBtn) verifyCodeBtn.disabled = true;
    if (verifyRecoveryCode) verifyRecoveryCode.disabled = true;
    
    // Variables
    let timer;
    let recoveryTimer;
    let verificationToken = '';
    let recoveryToken = '';
    let userEmail = '';
    let companyId = '';
    let recoveryEmail = '';
    let accountType = '';
    let recoveredCompanyId = '';
    
    // Check URL for company_id parameter and auto-fill the field
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('company_id')) {
        const companyIdFromUrl = urlParams.get('company_id');
        companyIdInput.value = companyIdFromUrl;
        companyId = companyIdFromUrl; // Set the variable for use in registration
        
        // Remove any previous errors if company ID is valid
        if (validateCompanyId(companyIdFromUrl)) {
            companyIdError.style.display = 'none';
            companyIdInput.classList.remove('error');
            // Focus on the next field (email) for better UX
            accountTypeSelect.focus();
        }
    }
    
    // Function to validate email
    function validateEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
    
    // Function to validate company ID
    function validateCompanyId(id) {
        const re = /^CCP\d{7}$/;
        return re.test(id);
    }
    
    // Function to show a specific step
    function showStep(stepNumber) {
        // Hide all steps
        formSteps.forEach(step => {
            step.classList.remove('active');
        });
        
        // Update step indicators
        steps.forEach(step => {
            const stepNum = parseInt(step.dataset.step);
            step.classList.remove('active', 'completed');
            
            if (stepNum < stepNumber) {
                step.classList.add('completed');
            } else if (stepNum === stepNumber) {
                step.classList.add('active');
            }
        });
        
        // Show the current step
        document.getElementById(`step-${stepNumber}`).classList.add('active');
        
        // Show main steps indicator and hide recovery steps indicator
        document.getElementById('main-steps').style.display = 'flex';
        document.getElementById('recovery-steps').style.display = 'none';
        
        // Reset the main form title to original
        const formTitle = document.querySelector('.form-container h2:first-of-type');
        if (formTitle) {
            formTitle.textContent = 'Register User Account';
        }
    }
    
    // Function to show recovery steps
    function showRecoveryStep(stepNumber) {
        // Hide all form steps
        formSteps.forEach(step => {
            step.classList.remove('active');
        });
        
        // Show the recovery step
        document.getElementById(`recover-step-${stepNumber}`).classList.add('active');
        
        // Hide main steps indicator and show recovery steps indicator
        document.getElementById('main-steps').style.display = 'none';
        const recoverySteps = document.getElementById('recovery-steps');
        recoverySteps.style.display = 'flex';
        
        // Update the active/completed status of each step
        const recoveryStepItems = recoverySteps.querySelectorAll('.step');
        recoveryStepItems.forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNum < stepNumber) {
                step.classList.add('completed');
            } else if (stepNum === stepNumber) {
                step.classList.add('active');
            }
        });
        
        // Update the main form title
        const formTitle = document.querySelector('.form-container h2:first-of-type');
        if (formTitle) {
            formTitle.textContent = 'Recover Company ID';
        }
    }
    
    // Function to start the resend timer
    function startResendTimer(isRecovery = false) {
        let seconds = 60;
        
        if (isRecovery) {
            resendRecoveryBtn.disabled = true;
            recoveryResendTimer.style.display = 'block';
            recoveryTimerCount.textContent = seconds;
            
            clearInterval(recoveryTimer);
            recoveryTimer = setInterval(() => {
                seconds--;
                recoveryTimerCount.textContent = seconds;
                
                if (seconds <= 0) {
                    clearInterval(recoveryTimer);
                    resendRecoveryBtn.disabled = false;
                    recoveryResendTimer.style.display = 'none';
                }
            }, 1000);
        } else {
            resendCodeBtn.disabled = true;
            resendTimer.style.display = 'block';
            timerCount.textContent = seconds;
            
            clearInterval(timer);
            timer = setInterval(() => {
                seconds--;
                timerCount.textContent = seconds;
                
                if (seconds <= 0) {
                    clearInterval(timer);
                    resendCodeBtn.disabled = false;
                    resendTimer.style.display = 'none';
                }
            }, 1000);
        }
    }
    
    // Function to send verification email
    function sendVerificationEmail() {
        const data = {
            account_type: accountType,
            company_id: companyId,
            email: userEmail,
            password: passwordInput.value
        };
        
        // Make actual API call to register user
        fetch('/api/register-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Verification email sent to:', userEmail);
                // Verification code will be sent by the server to the email
                startResendTimer();
            } else {
                alert('Error: ' + data.message);
                showStep(1);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while sending the verification email. Please try again.');
            showStep(1);
        });
    }
    
    // Function to send recovery email (renamed from sendRecoveryEmail to sendCompanyIdRecoveryEmail)
    function sendCompanyIdRecoveryEmail() {
        const data = {
            email: recoveryEmail
        };
        
        // Make actual API call to recover company ID
        fetch('/api/recover-company-id', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Recovery email sent to:', recoveryEmail);
                // Verification code will be sent by the server to the email
                
                // If it's a direct match, we skip the verification
                if (data.direct_match) {
                    alert('Your Company ID has been sent to your email.');
                    showStep(1);
                } else {
                    startResendTimer(true);
                }
            } else {
                alert('Error: ' + data.message);
                showRecoveryStep(1);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your request. Please try again.');
            showRecoveryStep(1);
        });
    }
    
    // Function to verify the registration code
    function verifyRegistrationCode() {
        let enteredCode = '';
        verificationInputs.forEach(input => {
            enteredCode += input.value;
        });
        enteredCode = enteredCode.toUpperCase(); // Ensure code is uppercase for comparison
        
        console.log("Attempting to verify user code:", enteredCode);
        
        // Make actual API call to verify user
        fetch('/api/verify-user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: enteredCode
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Move to success step
                showStep(3);
                
                // Set up automatic redirect to login page after 3 seconds
                setTimeout(function() {
                    window.location.href = '/login';
                }, 3000);
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during verification. Please try again.');
        });
    }
    
    // Function to verify the recovery code
    function verifyRecoveryCodeHandler() {
        let enteredCode = '';
        recoveryCodeInputs.forEach(input => {
            enteredCode += input.value;
        });
        enteredCode = enteredCode.toUpperCase(); // Ensure code is uppercase for comparison
        
        console.log("Attempting to verify recovery code:", enteredCode);
        
        // Make actual API call to verify company ID recovery
        fetch('/api/verify-company-id-recovery', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token: enteredCode
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Set the company ID from the response
                recoveredCompanyId = data.company_id;
                
                // Display the company ID in the third step
                if (recoveredCompanyIdInput) {
                    recoveredCompanyIdInput.value = recoveredCompanyId;
                }
                
                // Show the third step
                showRecoveryStep(3);
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during verification. Please try again.');
        });
    }
    
    // Set up verification code inputs
    function setupCodeInputs(inputs) {
        inputs.forEach((input, index) => {
            input.addEventListener('keyup', function(e) {
                // Auto-focus to next input on keyup
                if (e.key !== 'Backspace' && index < inputs.length - 1 && input.value.length === 1) {
                    inputs[index + 1].focus();
                }
                
                // Go back on backspace if current field is empty
                if (e.key === 'Backspace' && index > 0 && input.value.length === 0) {
                    inputs[index - 1].focus();
                }
                
                // Check if all inputs have values
                let allFilled = true;
                inputs.forEach(input => {
                    if (!input.value) {
                        allFilled = false;
                    }
                });
                
                // Enable verify button if all filled
                if (inputs === verificationInputs) {
                    verifyCodeBtn.disabled = !allFilled;
                } else {
                    verifyRecoveryCode.disabled = !allFilled;
                }
            });
            
            // Clear input on focus
            input.addEventListener('focus', function() {
                this.select();
            });
            
            // Only allow digits (0-9)
            input.addEventListener('input', function() {
                this.value = this.value.replace(/[^0-9]/g, '').substr(0, 1);
            });
            
            // Prevent non-digit characters on keypress
            input.addEventListener('keypress', function(e) {
                const key = String.fromCharCode(e.which);
                const regex = /[0-9]/;
                
                if (!regex.test(key)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }
    
    // Initialize verification code inputs
    setupCodeInputs(verificationInputs);
    setupCodeInputs(recoveryCodeInputs);
    
    // Event Listeners
    if (registerBtn) {
        registerBtn.addEventListener('click', function() {
            // Validate form inputs
            let isValid = true;
            
            // Validate account type
            if (!accountTypeSelect.value) {
                accountTypeError.style.display = 'block';
                accountTypeSelect.classList.add('error');
                isValid = false;
            } else {
                accountTypeError.style.display = 'none';
                accountTypeSelect.classList.remove('error');
                accountType = accountTypeSelect.value;
            }
            
            // Validate company ID
            if (!validateCompanyId(companyIdInput.value)) {
                companyIdError.style.display = 'block';
                companyIdInput.classList.add('error');
                isValid = false;
            } else {
                companyIdError.style.display = 'none';
                companyIdInput.classList.remove('error');
                companyId = companyIdInput.value;
            }
            
            // Validate email
            if (!validateEmail(emailInput.value)) {
                emailError.style.display = 'block';
                emailInput.classList.add('error');
                isValid = false;
            } else {
                emailError.style.display = 'none';
                emailInput.classList.remove('error');
                userEmail = emailInput.value;
            }
            
            // Validate password
            if (passwordInput.value.length < 8) {
                passwordError.style.display = 'block';
                passwordInput.classList.add('error');
                isValid = false;
            } else {
                passwordError.style.display = 'none';
                passwordInput.classList.remove('error');
            }
            
            // Validate password confirmation
            if (passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordError.style.display = 'block';
                confirmPasswordInput.classList.add('error');
                isValid = false;
            } else {
                confirmPasswordError.style.display = 'none';
                confirmPasswordInput.classList.remove('error');
            }
            
            if (isValid) {
                // Move to verification step
                showStep(2);
                sendVerificationEmail();
            }
        });
    }
    
    // Back to form button
    if (backToForm) {
        backToForm.addEventListener('click', function() {
            showStep(1);
        });
    }
    
    // Verify code button
    if (verifyCodeBtn) {
        verifyCodeBtn.addEventListener('click', function() {
            verifyRegistrationCode();
        });
    }
    
    // Company ID recovery flow
    if (recoverCompanyId) {
        recoverCompanyId.addEventListener('click', function(e) {
            e.preventDefault();
            showRecoveryStep(1);
        });
    }
    
    if (cancelRecovery) {
        cancelRecovery.addEventListener('click', function() {
            showStep(1);
        });
    }
    
    if (sendRecoveryEmailBtn) {
        sendRecoveryEmailBtn.addEventListener('click', function() {
            // Validate recovery email
            if (!validateEmail(recoveryEmailInput.value)) {
                recoveryEmailError.style.display = 'block';
                recoveryEmailInput.classList.add('error');
            } else {
                recoveryEmailError.style.display = 'none';
                recoveryEmailInput.classList.remove('error');
                recoveryEmail = recoveryEmailInput.value;
                
                // Move to verification step
                showRecoveryStep(2);
                sendCompanyIdRecoveryEmail();
            }
        });
    }
    
    if (backToRecoveryEmail) {
        backToRecoveryEmail.addEventListener('click', function() {
            showRecoveryStep(1);
        });
    }
    
    if (verifyRecoveryCode) {
        verifyRecoveryCode.addEventListener('click', function() {
            verifyRecoveryCodeHandler();
        });
    }
    
    // Resend code buttons
    if (resendCodeBtn) {
        resendCodeBtn.addEventListener('click', function() {
            if (!resendCodeBtn.disabled) {
                // Clear inputs
                verificationInputs.forEach(input => {
                    input.value = '';
                });
                verificationInputs[0].focus();
                
                // Resend verification email
                sendVerificationEmail();
            }
        });
    }
    
    if (resendRecoveryBtn) {
        resendRecoveryBtn.addEventListener('click', function() {
            if (!resendRecoveryBtn.disabled) {
                // Clear inputs
                recoveryCodeInputs.forEach(input => {
                    input.value = '';
                });
                recoveryCodeInputs[0].focus();
                
                // Resend recovery email
                sendCompanyIdRecoveryEmail();
            }
        });
    }
    
    // Copy recovered company ID button
    if (copyRecoveredIdBtn) {
        copyRecoveredIdBtn.addEventListener('click', function() {
            recoveredCompanyIdInput.select();
            document.execCommand('copy');
            
            // Show feedback
            const originalTitle = this.getAttribute('title');
            this.setAttribute('title', 'Copied!');
            setTimeout(() => {
                this.setAttribute('title', originalTitle);
            }, 2000);
        });
    }
    
    // Back to login button
    if (backToLoginBtn) {
        backToLoginBtn.addEventListener('click', function() {
            window.location.href = '/login';
        });
    }
    
    // Use for registration button
    if (useForRegistrationBtn) {
        useForRegistrationBtn.addEventListener('click', function() {
            // Return to registration form and fill in the company ID
            showStep(1);
            companyIdInput.value = recoveredCompanyId;
            companyId = recoveredCompanyId; // Set the variable for use in registration
            
            // Remove any previous errors
            companyIdError.style.display = 'none';
            companyIdInput.classList.remove('error');
        });
    }
    
    // Check all verification inputs to enable/disable verify buttons
    function checkVerificationInputs(inputs, button) {
        let allFilled = true;
        inputs.forEach(input => {
            if (!input.value) {
                allFilled = false;
            }
        });
        
        if (button) {
            button.disabled = !allFilled;
        }
    }
    
    // Add input event listeners to verification inputs
    verificationInputs.forEach(input => {
        input.addEventListener('input', function() {
            checkVerificationInputs(verificationInputs, verifyCodeBtn);
        });
    });
    
    recoveryCodeInputs.forEach(input => {
        input.addEventListener('input', function() {
            checkVerificationInputs(recoveryCodeInputs, verifyRecoveryCode);
        });
    });
});