sessionStorage.removeItem('ss_user_name');
sessionStorage.removeItem('ss_role');

$(document).ready(function () {
    var animating = false;
    var submitPhase1 = 1100;
    var submitPhase2 = 400;
    var logoutPhase1 = 800;
    
    var $login = $(".login");
    var $app = $(".app");

    function ripple(elem, e) {
        $(".ripple").remove();

        var elTop = elem.offset().top;
        var elLeft = elem.offset().left;
        var x = e.pageX - elLeft;
        var y = e.pageY - elTop;
        var $ripple = $("<div class='ripple'></div>");

        $ripple.css({ top: y, left: x });
        elem.append($ripple);
    };

    $(document).on("click", ".login__submit", function (e) {
        if (animating) return;

        animating = true;
        var that = this;

        ripple($(that), e);
        $(that).addClass("processing");

        var name = $("#name").val();
        var pass = $("#pass").val();
        var check = true;

        try {
            var server = io.connect('http://103.22.221.55:8080');
        } catch (e) {
            alert('Sorry, we couldn\'t connect. Please try again later \n\n' + e);
        }

        if (server !== undefined) {
            console.log("Connection established...");
        
            // send the values to the server
            server.emit('login', {
                user_name: name,
                user_password: pass
            });

            // alert error messages returned from the server
            server.on('alert', function (msg) {
                alert(msg);
                location.reload();
            });

            server.on('redirect', function (msg) {
                sessionStorage.setItem('ss_user_name', name);
                sessionStorage.setItem('ss_role', msg);
                window.location.assign('http://103.22.221.55:3006/menu');
            });
        }

        $(that).removeClass("success processing");
    });

    $(document).on("click", ".app__logout", function (e) {
        if (animating) return;
        
        $(".ripple").remove();
        
        animating = true;
        var that = this;

        $(that).addClass("clicked");

        setTimeout(function () {
            $app.removeClass("active");
            $login.show();
            $login.css("top");
            $login.removeClass("inactive");
        }, logoutPhase1 - 120);
        
        setTimeout(function () {
            $app.hide();
            animating = false;
            $(that).removeClass("clicked");
        }, logoutPhase1);
    });
});