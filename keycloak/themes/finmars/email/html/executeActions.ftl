<#outputformat "plainText">
<#assign requiredActionsText><#if requiredActions??><#list requiredActions><#items as reqActionItem>${msg("requiredAction.${reqActionItem}")}<#sep>, </#sep></#items></#list></#if></#assign>
</#outputformat>

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

${kcSanitize(msg("executeActionsBodyHtml",link, linkExpiration, realmName, requiredActionsText, linkExpirationFormatter(linkExpiration)))?no_esc}
</body>
</html>
