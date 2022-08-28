function submitter() {
    x = confirm("This will overwrite previous data!");
    if ( !x )
    {
        return false;
    }
}

function updater() {
    c = confirm("This will add new data in Patient Details.");
    if ( !c ) {
        return false;
    }
}

function remover() {
    r = confirm("This will delete all related data (including history) of the patient.")
    if ( !r )
    {
        return false;
    }
}

function remove_member() {
    l = confirm("Are you sure you want to remove this member? This will also delete releted patient history without affecting patient data.")
    if (!l)
    {
        return false;
    }
}

function change_name() {
    cc = confirm("This will change your username.")
    if (!cc)
    {
        return false;
    }
}

function change_password() {
    pp = confirm("Are you sure you want to change your pasword?")
    if ( !pp )
    {
        return false;
    }
}

function change_mail()
{
    mm = confirm("Your email address will change!")
    if ( !mm )
    {
        return false;
    }
}

function change_contact()
{
    ss = confirm("This will change your contact number!")
    if ( !ss )
    {
        return false;
    }
}

function showpass()
{
    var x = document.getElementById("exampleFormControlInput11");
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password"
    }
}

function showpass1()
{
    var l = document.getElementById("exampleFormControlInput12");
    if (l.type === "password") {
        l.type = "text";
    } else {
        l.type = "password"
    }
}

function showpass2()
{
    var m = document.getElementById("exampleFormControlInput13");
    if (m.type === "password") {
        m.type = "text";
    } else {
        m.type = "password"
    }
}