
// Usage:
// <script src="https://cdn.tslow.cn/AthenaTools/static/js/athena-output.js"
// data-target="table.athena-output"
// data-row-start="0" data-row-end="10"
// data-col-start="0" data-col-end="10"
// data-position-fixed="1"></script>

if (window.jQuery || window.jLoaded) {
    $(function () {

        var scriptTag = $("[src*='athena-output.js']").eq(0)
        var target = scriptTag.attr('data-target') || 'table.athena-output'
        var rowStart = scriptTag.attr('data-row-start') || 0
        var rowEnd = scriptTag.attr('data-row-end') || 65536
        var colStart = scriptTag.attr('data-col-start') || 0
        var colEnd = scriptTag.attr('data-col-end') || 65536
        var positionFixed = scriptTag.attr('data-position-fixed') || false

        var styleStr = 'style="z-index: 100;"'
        if (positionFixed) {
            styleStr = 'style="position: fixed; right: 40px; bottom: 10%; z-index: 100;"'
        }

        var form = $('<form class="athena-output" action="https://tools.athenagu.com/xls/" method="post" ' + styleStr +
            ' >' +
            '<input type="hidden" name="data" class="data"/>' +
            '<button type="submit" class="btn btn-primary">导出</button>' +
            '</form>')

        scriptTag.after(form)

        $('form.athena-output').submit(function () {

            var data = []
            var table = $(target).eq(0)

            if (table.length === 0) {
                var tables = $('table')
                for (var i=0;i<tables.length;i++) {
                    table = tables.eq(i)
                    if ($.trim(table.text())) {
                        break
                    }
                }
            }

            var trs = table.find('tr')

            for(var i=0;i<trs.length;i++){
                if (i < rowStart || i > rowEnd) {
                    continue
                }
                var tr = trs.eq(i)
                var tds = tr.find('th,td')
                for(var j=0;j<tds.length;j++){
                var td = tds.eq(j)
                    if (j < colStart || j > colEnd) {
                        continue
                    }
                    data.push({"row": i, "col": j, "value": $.trim(td.text())})
                }
            }
            data = JSON.stringify(data)
            $(this).find('.data').val(data);
        })

    })
} else {
    console.log('Load JQuery by AthenaTools')
    window.jLoaded = true
    document.write('<script src="https://tools.athenagu.com/static/js/jquery-1.10.2.js"><\/script>')
    document.write('<script src="https://cdn.tslow.cn/AthenaTools/static/js/athena-output.js"><\/script>')
}


