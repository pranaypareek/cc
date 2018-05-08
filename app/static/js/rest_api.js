$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#item_id").val(res.id);
        $("#item_name").val(res.name);
        $("#item_price").val(res.price);
        if (res.available == true) {
            $("#item_available").val("true");
        } else {
            $("#item_available").val("false");
        }
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#item_name").val("");
        $("#item_price").val("");
        $("#item_available").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Item
    // ****************************************

    $("#create-btn").click(function () {

        var name = $("#item_name").val();
        var price = $("#item_price").val();
        var available = $("#item_available").val() == "true";

        var data = {
            "name": name,
            "price": price,
            "available": available
        };

        var ajax = $.ajax({
            type: "POST",
            url: "/items",
            contentType:"application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    // ****************************************
    // Update a Item
    // ****************************************

    $("#update-btn").click(function () {

        var item_id = $("#item_id").val();
        var name = $("#item_name").val();
        var price = $("#item_price").val();
        var available = $("#item_available").val() == "true";

        var data = {
            "name": name,
            "price": price,
            "available": available
        };

        var ajax = $.ajax({
                type: "PUT",
                url: "/items/" + item_id,
                contentType:"application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve a Item
    // ****************************************

    $("#retrieve-btn").click(function () {

        var item_id = $("#item_id").val();

        var ajax = $.ajax({
            type: "GET",
            url: "/items/" + item_id,
            contentType:"application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Item
    // ****************************************

    $("#delete-btn").click(function () {

        var item_id = $("#item_id").val();

        var ajax = $.ajax({
            type: "DELETE",
            url: "/items/" + item_id,
            contentType:"application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Item with ID [" + res.id + "] has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#item_id").val("");
        clear_form_data()
    });

    // ****************************************
    // Search for a Item
    // ****************************************

    $("#search-btn").click(function () {

        var name = $("#item_name").val();
        var price = $("#item_price").val();
        var available = $("#item_available").val() == "true";

        var queryString = ""

        if (name) {
            queryString += 'name=' + name
        }
        if (price) {
            if (queryString.length > 0) {
                queryString += '&price=' + price
            } else {
                queryString += 'price=' + price
            }
        }
        if (available) {
            if (queryString.length > 0) {
                queryString += '&available=' + available
            } else {
                queryString += 'available=' + available
            }
        }

        var ajax = $.ajax({
            type: "GET",
            url: "/items?" + queryString,
            contentType:"application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            $("#search_results").append('<table class="table-striped">');
            var header = '<tr>'
            header += '<th style="width:10%">ID</th>'
            header += '<th style="width:40%">Name</th>'
            header += '<th style="width:40%">Price</th>'
            header += '<th style="width:10%">Available</th></tr>'
            $("#search_results").append(header);
            for(var i = 0; i < res.length; i++) {
                item = res[i];
                var row = "<tr><td>"+item.id+"</td><td>"+item.name+"</td><td>"+item.price+"</td><td>"+item.available+"</td></tr>";
                $("#search_results").append(row);
            }

            $("#search_results").append('</table>');

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

})
