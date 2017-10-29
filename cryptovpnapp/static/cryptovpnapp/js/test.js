var baseResourceUrl = "api/1.0/"
var baseAuthUrl = "api/1.0/rest-auth/"

var registerUrl = "/api/1.0/rest-auth/registration/";
var loginUrl = "/api/1.0/rest-auth/login/";
var logoutUrl = "/api/1.0/rest-auth/login/";
var userDetailsUrl = "/api/1.0/rest-auth/user/";
var passwordResetUrl = "/api/1.0/rest-auth/password/reset/";
var changePasswordUrl = "/api/1.0/rest-auth/password/change/";
var servicesUrl = "/api/1.0/services/";
var subscriptionsUrl = "/api/1.0/subscriptions/";
var invoicesUrl = "/api/1.0/invoices/";
var refundRequestUrl = "/api/1.0/refund_requests/";
var commentUrl = "/api/1.0/comments/";

var registerData = {
    username: "testuser",
    password1: "q1w2e3r4",
    password2: "q1w2e3r4",
    email: "abc@xyz.com"
};

var loginData = {
    username: "testuser",
    password: "q1w2e3r4"
};

var orderSubscriptionData = {
    subscription_type: 0,
    coin: "BTC"
};

var refundRequestData = {
    amount_requested: 0.05,
    text: "Please help!"
};

var commentData = {
    text: "Gimme my money!"
};

var passwordResetData = {
    email: "abc@xyz.com"
};

var changePasswordData = {
    old_password: "q1w2e3r4",
    new_password1: "0o9i8u7y",
    new_password2: "0o9i8u7y"
};

function logout(){
    return $.ajax(loginUrl, {method: "POST"})
}

function changePassword(response){
    return $.ajax(changePasswordUrl, {method: "POST", data: changePasswordData);
}

function sendPasswordReset(response){
    return $.ajax(passwordResetUrl, {method: "POST", data: passwordResetData});
}

function viewRefundRequest(response){
    return $.ajax(refundRequestURL, {method: "POST"});
}

function createComment(response){
    var refundRequest = response.result;
    commentData.refund_request = refundRequest.id;
    return $.ajax(commentUrl, {method: "POST", data: commentData});
}

function createRefundRequest(response){
    var invoice = response.results[0]
    refundRequestData.invoice = invoice.id;
    return $.ajax(refundRequestURL, {method: "POST", data: refundRequestData});
}

function viewInvoices(response){
    return $.ajax(invoicesUrl, {method: "GET"});
}

function checkSubscription(response){
    return $.ajax(subscriptionsUrl, {method: "GET"});
}

function orderSubscription(response){
    return $.ajax(subscriptionsUrl, {method: "POST", data=orderSubscriptionData});
}

function getServices(response){
    return $.ajax(servicesUrl, {method: "GET"});
}

function getUserDetails(response){
   return $.ajax(userDetailsUrl, {method: "GET"});
}

function setAuthHeader(response){
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("Authorization", "JWT " + response.token);
            }
        }
    })
    return response;
}

function login(response){
    return $.ajax(loginUrl, {method: "POST", data: loginData}).then(setAuthHeader);
}

function register(){
    return $.ajax(registerUrl, {method: "POST", data: registerData});
}

function runTests(){
    register
        .then(login
        .then(getUserDetails
        .then(getServices()
        .then(orderSubscription()
        .then(checkSubscription()
        .then(viewInvoices)
        .then(createRefundRequest()
        .then(createComment()
        .then(viewRefundRequest()
        .then(sendPasswordReset())
        .then(changePassword()
        .then(logout()
        ))))))))))
    )
}