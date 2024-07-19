$(document).ready(function(){
    function scrollToBottom() {
        $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
    }

    function adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }

    $('#chat-input').on('input', function(){
        adjustTextareaHeight(this);
    });

    $('#send-btn').on('click', function(){
        var userMessage = $('#chat-input').val();
        if (userMessage.trim() === '') return;
        $('#chat-box').append('<div class="chat-message user">' + userMessage.replace(/\n/g, '<br>') + '</div>');
        $('#chat-input').val('');
        adjustTextareaHeight($('#chat-input')[0]); // Reset the height after clearing the input

        var url = $('#chat-input').data('url') + '?message=' + encodeURIComponent(userMessage);

        // Open EventSource connection
        var eventSource = new EventSource(url);
        var assistantMessageDiv = $('<div class="chat-message assistant"></div>');
        $('#chat-box').append(assistantMessageDiv);
        scrollToBottom();

        var fullMessage = "";

        eventSource.onmessage = function(event) {
            var assistantMessage = event.data;                   
            
            fullMessage += assistantMessage;
            fullMessage = fullMessage.replace(/\\n/g, '<br>');
        
            // Update the div with the full concatenated message
            assistantMessageDiv.html(fullMessage);
            scrollToBottom();
        };

        eventSource.onerror = function(error) {
            console.error("EventSource error:", error);
            eventSource.close();
        };

        eventSource.onopen = function() {
            console.log("EventSource connection opened");
        };

        eventSource.onclose = function() {
            console.log("EventSource connection closed");
        };
    });

    $('#chat-input').on('keypress', function(e){
        if(e.which == 13 && !e.shiftKey){
            $('#send-btn').click();
            return false;
        }
    });

    // Menu toggle
    $('.menu-btn').on('click', function() {
        $('.menu').toggle();
    });

    // // Hover effect for the menu button
    // $('.menu-btn').hover(
    //     function() {
    //         $(this).find('.default').hide();
    //         $(this).find('.hover').show();
    //     },
    //     function() {
    //         $(this).find('.hover').hide();
    //         $(this).find('.default').show();
    //     }
    // );

    // Automatically scroll to the bottom on page load
    scrollToBottom();
});
