
if (window.jQuery) {
    $(function () {

        var form = $('<form class="athena-output" action="https://tools.athenagu.com/xls/" method="post" ' +
            'style="position: fixed; right: 50px; bottom: 10%;">' +
            '<input type="hidden" name="data" class="data"/>' +
            '<button type="submit" class="btn btn-primary">导出</button>' +
            '</form>')

        $('body').append(form)

        $('.athena-output').submit(function () {
            var table = $('table').eq(0)
            var data = []
            var trs = table.find('tr')
            for(var i=0;i<trs.length;i++){
              var tr = trs.eq(i)
              var tds = tr.find('th,td')
              for(var j=0;j<tds.length;j++){
                  var td = tds.eq(j)
                  data.push({"row": i, "col": j, "value": $.trim(td.text())})
              }
            }
            data = JSON.stringify(data)
            $(this).find('.data').val(data);
        })
    })
} else {
    document.write('<script src="https://tools.athenagu.com/static/js/jquery-1.10.2.js"><\/script>')
    document.write('<script src="https://tools.athenagu.com/static/js/athena-output.js"><\/script>')
}


