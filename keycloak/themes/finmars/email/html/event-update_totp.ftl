<html>
<body>

<style>
    body {
        background: #000;
        color: #fff;
        padding: 16px;
        font-family: sans-serif;
        font-size: 14px;
    }
    body a {
        color: #fff
    }
</style>

<div>
    <img src="${url.resourcesUrl}/img/logo.png" />
</div>

${kcSanitize(msg("eventUpdateTotpBodyHtml",event.date, event.ipAddress))?no_esc}
</body>
</html>
