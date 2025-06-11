document.addEventListener('DOMContentLoaded', () => {
    // Mobile navigation toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.getElementById('main-nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', !isExpanded);
            navMenu.classList.toggle('show');
        });
    }

    // Custom Modal Functions (reusable across pages)
    // Make sure the modal HTML structure is present in pages that use it
    const customModalOverlay = document.getElementById('customModalOverlay');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    let modalConfirmCallback = null;

    if (customModalOverlay && modalTitle && modalMessage && modalCloseBtn) {
        // Initial setup for modal close (for 'OK' button)
        modalCloseBtn.addEventListener('click', () => {
            if (modalConfirmCallback) {
                modalConfirmCallback(); // Execute callback for confirmation
                modalConfirmCallback = null; // Reset callback
            }
            hideModal();
        });

        // Add a cancel button for confirmation dialogs, if it doesn't exist
        let modalCancelBtn = document.getElementById('modalCancelBtn');
        if (!modalCancelBtn) {
            modalCancelBtn = document.createElement('button');
            modalCancelBtn.id = 'modalCancelBtn';
            modalCancelBtn.textContent = 'Cancel';
            modalCancelBtn.className = 'ml-3 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-full';
            customModalOverlay.querySelector('.custom-modal-content').appendChild(modalCancelBtn);
        }
        modalCancelBtn.addEventListener('click', hideModal); // Always close modal on cancel

        // Export showModal and hideModal to global scope or as methods if needed
        // For simplicity in this HTML context, making them global
        window.showModal = (title, message, onConfirm = null) => {
            modalTitle.textContent = title;
            modalMessage.innerHTML = message; // Use innerHTML for potential Markdown/HTML
            
            modalConfirmCallback = onConfirm;

            // Adjust button text and visibility based on whether it's a confirmation
            if (onConfirm) {
                modalCloseBtn.textContent = 'Confirm';
                modalCancelBtn.style.display = 'inline-block';
                // Remove existing click listener to avoid multiple calls if button reused
                modalCloseBtn.removeEventListener('click', hideModal);
            } else {
                modalCloseBtn.textContent = 'OK';
                modalCancelBtn.style.display = 'none';
                // Add default close listener if not already there
                modalCloseBtn.addEventListener('click', hideModal);
            }
            customModalOverlay.style.display = 'flex';
        };

        window.hideModal = () => {
            customModalOverlay.style.display = 'none';
            modalConfirmCallback = null; // Clear callback on hide
            // Ensure button state is reset for next use
            modalCloseBtn.textContent = 'OK';
            modalCancelBtn.style.display = 'none';
            modalCloseBtn.removeEventListener('click', modalConfirmCallback); // Remove specific confirm listener
            modalCloseBtn.addEventListener('click', hideModal); // Add default close
        };
    } else {
        console.warn("Custom modal elements not found. Modal functionality may not work.");
        // Fallback for environments without custom modal HTML
        window.showModal = (title, message) => alert(`${title}\n\n${message}`);
        window.hideModal = () => {};
    }
});