<script type="text/javascript">
    //获取元素
    let lis=document.querySelectorAll('#menu>ul>li')
    // 遍历获得单个元素
    for(let i=0;i<lis.length;i++){
        // 为单个元素绑定鼠标移入事件
        lis[i].addEventListener('mouseover',function(){
            // 消除设置的默认active
            for(let j=0;j<lis.length;j++){
                lis[j].className=''
            }
            lis[i].className='active'
        })
        // 为单个元素绑定鼠标移出事件
        lis[i].addEventListener('mouseout',function(){
            lis[i].className=''
        })
    }
</script>