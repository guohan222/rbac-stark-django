
// 二级菜单
const menuTitle = document.querySelectorAll('.multi-menu .item > .title')
menuTitle.forEach(title => {
    title.addEventListener('click',function (){
        const body = this.nextElementSibling
        body.classList.toggle('hidden')
    })
})


