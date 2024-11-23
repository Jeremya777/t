// static/js/validation.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("validation.js caricato correttamente.");

    // Trova tutti i form nella pagina
    const forms = document.querySelectorAll("form");

    forms.forEach((form) => {
        const inputs = form.querySelectorAll("input");

        // Funzione per mostrare un messaggio di errore accanto all'input
        const showError = (input, message) => {
            clearError(input);
            const errorElement = document.createElement("span");
            errorElement.classList.add("error-message", "text-red-500", "text-sm");
            errorElement.textContent = message;
            input.parentElement.appendChild(errorElement);
            input.classList.add("border-red-500");
        };

        // Funzione per rimuovere il messaggio di errore
        const clearError = (input) => {
            const errorElement = input.parentElement.querySelector(".error-message");
            if (errorElement) {
                errorElement.remove();
            }
            input.classList.remove("border-red-500");
        };

        // Funzione di validazione per ogni campo
        const validateField = (input) => {
            const name = input.id;
            const value = input.value.trim();
            let isValid = true;
            let message = "";

            if (name === 'username') {
                if (value.length < 3) {
                    message = "Il nickname deve essere lungo almeno 3 caratteri.";
                    isValid = false;
                }
            } else if (name === 'email') {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    message = "Per favore, inserisci un'email valida.";
                    isValid = false;
                }
            } else if (name === 'password') {
                const passwordRegex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{7,}$/;
                if (!passwordRegex.test(value)) {
                    message = "La password deve avere almeno 7 caratteri, un numero, un carattere speciale e una maiuscola.";
                    isValid = false;
                }
            } else if (name === 'password_confirm') {
                const passwordInput = form.querySelector("input[name='password']");
                if (passwordInput && value !== passwordInput.value.trim()) {
                    message = "Le password non coincidono.";
                    isValid = false;
                }
            }

            if (!isValid) {
                showError(input, message);
            } else {
                clearError(input);
            }

            return isValid;
        };

        // Aggiunge l'evento "keyup" per validare in tempo reale
        inputs.forEach(input => {
            input.addEventListener("keyup", () => {
                validateField(input);
            });
        });

        // Gestisce l'evento submit del form per evitare l'invio se ci sono errori
        form.addEventListener("submit", (e) => {
            let isFormValid = true;
            inputs.forEach(input => {
                if (!validateField(input)) {
                    isFormValid = false;
                }
            });

            if (!isFormValid) {
                e.preventDefault();
            }
        });
    });
});
