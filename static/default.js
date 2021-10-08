function toggle_like(post_id, type) {
    console.log(post_id, type)
    let $a_like = $(`#${post_id} a[aria-label='${type}']`)
    let $i_like = $a_like.find("i")
    let selects = {"heart": "fa-heart", "star": "fa-star", "like": "fa-thumbs-up"}
    let dislikes = {"heart": "fa-heart-o", "star": "fa-star-o", "like": "fa-thumbs-o-up"}
    if ($i_like.hasClass(selects[type])) {
        $.ajax({
            type: "POST",
            url: "/update_like",
            data: {
                post_id_give: post_id,
                type_give: type,
                action_give: "unlike"
            },
            success: function (response) {
                console.log("unlike")
                $i_like.addClass(dislikes[type]).removeClass(selects[type])
                $a_like.find("span.like-num").text(num2str(response["count"]))
            }
        })
    } else {
        $.ajax({
            type: "POST",
            url: "/update_like",
            data: {
                post_id_give: post_id,
                type_give: type,
                action_give: "like"
            },
            success: function (response) {
                console.log("like")
                $i_like.addClass(selects[type]).removeClass(dislikes[type])
                $a_like.find("span.like-num").text(num2str(response["count"]))
            }
        })

    }
}

function post() {
    let comment = $("#textarea-post").val()
    let today = new Date().toISOString()
    if (comment === "") {
        alert("아무 내용도 찾지 못했어요 :C\n내용을 적어주세요!")
        $("#textarea-post").focus()
    } else {
        $.ajax({
            type: "POST",
            url: "/posting",
            data: {
                comment_give: comment,
                date_give: today
            },
            success: function (response) {
                $("#modal-post").removeClass("is-active")
                window.location.reload()
            }
        })
    }
}

function time2str(date) {
    let today = new Date()
    let time = (today - date) / 1000 // 초

    if (time < 60) {
        return parseInt(time) + "초 전"
    }
    time = time / 60
    if (time < 60) {
        return parseInt(time) + "분 전"
    }
    time = time / 60  // 시간
    if (time < 24) {
        return parseInt(time) + "시간 전"
    }
    time = time / 24
    if (time < 7) {
        return parseInt(time) + "일 전"
    }
    return `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`
}

function num2str(count) {
    if (count > 10000) {
        return parseInt(count / 1000) + "k"
    }
    if (count > 500) {
        return parseInt(count / 100) / 10 + "k"
    }
    if (count === 0) {
        return ""
    }
    return count
}

function get_posts(username) {
    if (username == undefined) {
        username = ""
    }
    $("#post-box").empty()
    $.ajax({
        type: "GET",
        url: `/get_posts?username_give=${username}`,
        data: {},
        success: function (response) {
            if (response["result"] === "success") {
                let posts = response["posts"]
                for (let i = 0; i < posts.length; i++) {
                    let post = posts[i]
                    let time_post = new Date(post["date"])
                    let time_before = time2str(time_post)
                    let class_heart = post['heart_by_me'] ? "fa-heart" : "fa-heart-o"
                    let count_heart = post['count_heart']
                    let class_star = post['star_by_me'] ? "fa-star" : "fa-star-o"
                    let count_star = post['count_star']
                    let class_like = post['like_by_me'] ? "fa-thumbs-up" : "fa-thumbs-o-up"
                    let count_like = post['count_like']
                    let html_temp = `<div class="box" id="${post["_id"]}">
                                        <article class="media">
                                            <div class="media-left">
                                                <a class="image is-64x64" href="/user/${post['username']}">
                                                    <img class="is-rounded" src="/static/${post['profile_pic_real']}"
                                                         alt="Image">
                                                </a>
                                            </div>
                                            <div class="media-content">
                                                <div class="content">
                                                    <p>
                                                        <strong>${post['profile_name']}</strong> <small>@${post['username']}</small> <small>${time_before}</small>
                                                        <br>
                                                        ${post['comment']}
                                                    </p>
                                                </div>
                                                <nav class="level is-mobile">
                                                    <div class="level-left">
                                                        <a class="level-item is-sparta" aria-label="heart" onclick="toggle_like('${post['_id']}', 'heart')">
                                                            <span class="icon is-small"><i class="fa ${class_heart}"
                                                                                           aria-hidden="true"></i></span>&nbsp;<span class="like-num">${num2str(count_heart)}</span>
                                                        </a>
                                                        <a class="level-item is-sparta" aria-label="star" onclick="toggle_like('${post['_id']}', 'star')">
                                                            <span class="icon is-small"><i class="fa ${class_star}"
                                                                                           aria-hidden="true"></i></span>&nbsp;<span class="like-num">${num2str(count_star)}</span>
                                                        </a>
                                                        <a class="level-item is-sparta" aria-label="like" onclick="toggle_like('${post['_id']}', 'like')">
                                                            <span class="icon is-small"><i class="fa ${class_like}"
                                                                                           aria-hidden="true"></i></span>&nbsp;<span class="like-num">${num2str(count_like)}</span>
                                                        </a>
                                                    </div>

                                                </nav>
                                            </div>
                                        </article>
                                    </div>`
                    $("#post-box").append(html_temp)
                }
            }
        }
    })
}

function sign_out() {
    $.removeCookie('mytoken', {path: '/'});
    alert('로그아웃!')
    window.location.href = "/login"
}

function update_profile() {
    let name = $('#input-name').val()
    let file = $('#input-pic')[0].files[0]
    let about = $("#textarea-about").val()
    let form_data = new FormData()
    form_data.append("file_give", file)
    form_data.append("name_give", name)
    form_data.append("about_give", about)
    console.log(name, file, about, form_data)

    $.ajax({
        type: "POST",
        url: "/update_profile",
        data: form_data,
        cache: false,
        contentType: false,
        processData: false,
        success: function (response) {
            if (response["result"] == "success") {
                alert(response["msg"])
                window.location.reload()
            }
        }
    });
}