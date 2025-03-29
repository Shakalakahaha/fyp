// register_company.js - Script for the company registration multi-step form

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const steps = document.querySelectorAll('.step');
    const formSteps = document.querySelectorAll('.form-step');
    const nextToVerification = document.getElementById('next-to-verification');
    const verifyCode = document.getElementById('verify-code');
    const companyNameInput = document.getElementById('company-name');
    const companyEmailInput = document.getElementById('company-email');
    const companyNameError = document.getElementById('company-name-error');
    const companyEmailError = document.getElementById('company-email-error');
    const resendCodeBtn = document.getElementById('resend-code-btn');
    const resendTimer = document.getElementById('resend-timer');
    const timerCount = document.getElementById('timer-count');
    const verificationInputs = document.querySelectorAll('.verification-code-input');
    const companyIdDisplay = document.getElementById('company-id');
    const emailDisplay = document.getElementById('email-display');
    const copyIdBtn = document.getElementById('copy-id');
    
    // Variables
    let timer;
    let verificationToken = '';
    let companyEmail = '';
    let companyName = '';
    
    // Function to validate email
    function validateEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
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
    }
    
    // Initialize copy button
    if (copyIdBtn) {
        copyIdBtn.addEventListener('click', function() {
            if (companyIdDisplay && companyIdDisplay.value) {
                companyIdDisplay.select();
                document.execCommand('copy');
                
                // Visual feedback
                this.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    this.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            }
        });
    }
    
    // Event listeners
    nextToVerification.addEventListener('click', function() {
        // Validate inputs
        let isValid = true;
        
        if (!companyNameInput.value.trim()) {
            companyNameError.style.display = 'block';
            companyNameInput.parentElement.parentElement.classList.add('error');
            isValid = false;
        } else {
            companyNameError.style.display = 'none';
            companyNameInput.parentElement.parentElement.classList.remove('error');
            companyName = companyNameInput.value.trim();
        }
        
        if (!validateEmail(companyEmailInput.value)) {
            companyEmailError.style.display = 'block';
            companyEmailInput.parentElement.parentElement.classList.add('error');
            isValid = false;
        } else {
            companyEmailError.style.display = 'none';
            companyEmailInput.parentElement.parentElement.classList.remove('error');
            companyEmail = companyEmailInput.value.trim();
        }
        
        if (isValid) {
            showStep(2);
            sendVerificationEmail();
        }
    });
    
    verifyCode.addEventListener('click', function() {
        verifyRegistrationCode();
    });
    
    resendCodeBtn.addEventListener('click', function() {
        // Clear inputs
        verificationInputs.forEach(input => {
            input.value = '';
        });
        verificationInputs[0].focus();
        
        // Resend verification email
        sendVerificationEmail();
    });
    
    // Ensure the verify button is disabled initially
    if (verifyCode) {
        verifyCode.disabled = true;
    }
    
    // Function to start the resend timer
    function startResendTimer() {
        let seconds = 60;
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
    
    // Function to send verification email
    function sendVerificationEmail() {
        const data = {
            company_name: companyName,
            company_email: companyEmail
        };
        
        // Display the email in the verification step
        if (emailDisplay) {
            emailDisplay.textContent = companyEmail;
        }
        
        // Make actual API call to register company
        fetch('/api/register-company', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Verification email sent to:', companyEmail);
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
    
    // Function to verify the code
    function verifyRegistrationCode() {
        let enteredCode = '';
        verificationInputs.forEach(input => {
            enteredCode += input.value;
        });
        enteredCode = enteredCode.toUpperCase(); // Ensure code is uppercase for comparison
        
        console.log("Attempting to verify code:", enteredCode);
        
        // Make actual API call to verify company
        fetch('/api/verify-company', {
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
                const companyId = data.company_id;
                companyIdDisplay.value = companyId;
                
                // Move to success step
                showStep(3);
                
                // Don't immediately redirect to user registration
                // Let user see their company ID first
                // window.location.href = '/register-user?company_id=' + encodeURIComponent(companyId);
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
    verificationInputs.forEach((input, index) => {
        input.addEventListener('keyup', function(e) {
            if (e.key !== 'Backspace' && index < verificationInputs.length - 1 && input.value.length === 1) {
                verificationInputs[index + 1].focus();
            }
            
            if (e.key === 'Backspace' && index > 0 && input.value.length === 0) {
                verificationInputs[index - 1].focus();
            }
            
            // Check if all inputs have values
            let allFilled = true;
            verificationInputs.forEach(input => {
                if (!input.value) {
                    allFilled = false;
                }
            });
            
            verifyCode.disabled = !allFilled;
        });
        
        // Clear input on focus
        input.addEventListener('focus', function() {
            this.select();
        });
        
        // Only allow digits (0-9)
        input.addEventListener('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '').substr(0, 1);
            
            // Check if all inputs have values after each input
            let allFilled = true;
            verificationInputs.forEach(input => {
                if (!input.value) {
                    allFilled = false;
                }
            });
            
            verifyCode.disabled = !allFilled;
            
            // Move to next input if not the last
            if (this.value && index < verificationInputs.length - 1) {
                verificationInputs[index + 1].focus();
            }
        });
        
        // Handle paste events - allow more efficiently
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            const clipboardData = e.clipboardData || window.clipboardData;
            const pastedText = clipboardData.getData('Text').trim();
            
            if (/^\d+$/.test(pastedText)) {
                // If it's all digits, we can use it
                const digits = pastedText.split('');
                
                // Fill as many inputs as we have digits
                for (let i = 0; i < Math.min(digits.length, verificationInputs.length - index); i++) {
                    verificationInputs[index + i].value = digits[i];
                }
                
                // Focus on the next empty input or the last input
                let nextEmptyIndex = -1;
                for (let i = 0; i < verificationInputs.length; i++) {
                    if (!verificationInputs[i].value) {
                        nextEmptyIndex = i;
                        break;
                    }
                }
                
                if (nextEmptyIndex !== -1) {
                    verificationInputs[nextEmptyIndex].focus();
                } else {
                    verificationInputs[verificationInputs.length - 1].focus();
                }
                
                // Check if all inputs have values
                let allFilled = true;
                verificationInputs.forEach(input => {
                    if (!input.value) {
                        allFilled = false;
                    }
                });
                
                verifyCode.disabled = !allFilled;
            }
        });
    });

    // Prevent dropdown from closing too quickly by adding a small delay
    document.querySelectorAll('.dropdown').forEach(dropdown => {
        let timeoutId;
        
        dropdown.addEventListener('mouseenter', () => {
            clearTimeout(timeoutId);
            dropdown.querySelector('.dropdown-menu').style.opacity = '1';
            dropdown.querySelector('.dropdown-menu').style.visibility = 'visible';
            dropdown.querySelector('.dropdown-menu').style.transform = 'translateY(0)';
        });
        
        dropdown.addEventListener('mouseleave', () => {
            timeoutId = setTimeout(() => {
                dropdown.querySelector('.dropdown-menu').style.opacity = '0';
                dropdown.querySelector('.dropdown-menu').style.visibility = 'hidden';
                dropdown.querySelector('.dropdown-menu').style.transform = 'translateY(10px)';
            }, 300); // 300ms delay before closing
        });
    });
}); 