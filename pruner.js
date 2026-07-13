(function() {
    // Check memory and if possible, trigger GC
    const checkMemory = () => {
        // This is a hint to the browser/React
        // If the browser is launched with --enable-javascript-harmony, 
        // you might be able to trigger garbage collection.
        if (typeof window.gc === 'function') {
            window.gc();
        }
    };

    // Periodically check memory usage
    const prune = () => {
        const bubbles = document.querySelectorAll('.conversation-container');
        if (bubbles.length > 5) {
            console.log("Conversation context is getting heavy.");
        }
        checkMemory();
    };

    // Run check on a reasonable interval
    setInterval(prune, 5000); 
})();
