import sys
import wsgiref.handlers

sys.path.append('modules')
from base import *
from models import *
from api import dispatcher
from django.utils.html import linebreaks, escape, urlize
from django.utils.feedgenerator import Rss201rev2Feed, Atom1Feed
from mimetypes import types_map
from google.appengine.api import mail
import time
from pyip import *

# {{{ Handlers
# {{{ Plog
class NewPost(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            self.current_page = "new"
            self.template_values.update({
                'mode' : 'new',
                })
            self.render(self.theme.editpost_page)

    def post(self):
        if self.chk_admin():
            title = self.param('title')
            content = self.param('post_content')
            tags = split_tags(self.param('tags'))
            type = self.param('type')
            pub_type = self.param('pub_type')

            try:
                new_article(title = title, author = self.login_user, content = content, tags = tags, type = type, pub_type = pub_type)

                self.redirect(settings.home_page)
            except db.BadValueError, e:
                self.redirect(settings.home_page)

class NewComment(PlogRequestHandler):
    def post(self):
        content = self.param('comment_content')
        postid = self.param('postid')
        nick = self.param('nick')
        site = self.param('site')
        #post = Post.get_by_id(int(postid))
        email = self.param('email')
        ip = self.request.remote_addr

        uri = self.request.uri
        try:
            if self.chk_login():
                who = self.login_user
            else:
                who = users.User(email)
        except:
            self.redirect('%s/post/%s#comments' % (settings.app_root, postid))
            return

        try:
            new_comment(postid = postid, content = content, author = who, nick = nick, site = site, ip = ip)
            self.redirect('%s/post/%s' % (settings.app_root, postid))
        except db.BadValueError, e:
            self.redirect(settings.home_page)

class EditPost(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            self.current_page = "new"
            postid = self.request.path[len(settings.app_root) + len('/admin/editpost/'):]
            post = Post.get_by_id(int(postid))
            self.template_values.update({
                'post' : post,
                'mode' : 'edit',
                })
            self.render(self.theme.editpost_page)

    def post(self):
        if self.chk_admin():
            postid = self.request.path[len(settings.app_root) + len('/admin/editpost/'):]
            edit_article(
                    postid = postid,
                    title = self.param('title'),
                    content = self.param('post_content'),
                    tags = split_tags(self.param('tags')),
                    slug = self.param('slug'),
                    type = self.param('type'),
                    pub_type = self.param('pub_type')
                    )

            self.redirect(settings.home_page)

class DeletePost(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            postid = self.param('postid')
            delete_post(int(postid))
            self.redirect(settings.home_page)

class DeleteComment(PlogRequestHandler):
    def get(self):
        if self.chk_login():
            commentid = self.param('commentid')
            postid = delete_comment(commentid, self.login_user, self.is_admin)
            if postid:
                self.redirect('%s/post/%d' % (settings.app_root, postid))
            else:
                self.redirect(settings.home_page)

def get_wrap(f):
    def get_with_trackip(args):
        adjustTimeZone = datetime.timedelta(hours = 8)
        data = IPDataBlog(ip = args.request.remote_addr, uri = args.request.uri)
        data.atime += adjustTimeZone
        data.put()
        return f(args)
    get_with_trackip.func_name = f.func_name
    return get_with_trackip

class PostList(PlogRequestHandler):
    @get_wrap
    def get(self):
        self.current_page = "home"
        page = 0
        show_prev = False
        show_next = False

        all_posts = Post.all().filter('type = ', 'post')
        if not self.is_admin:
            all_posts.filter('pub_type = ', 'public')

        max_page = (post_count() - 1) / config.posts_per_page

        if self.request.path.startswith('%s/post/page/' % settings.app_root):
            page = int(self.request.path[len(settings.app_root) + len('/post/page/'):])

            if page < 0 or page > max_page:
                self.error_404()
                return

        posts = all_posts.order('-date').fetch(config.posts_per_page, offset = page * config.posts_per_page)

        show_prev = not (page == 0)
        show_next = not (page == max_page)

        if not posts:
            show_prev = False
            show_next = False

        self.template_values.update({
                'posts' : posts,
                'show_prev' : show_prev,
                'show_next' : show_next,
                'show_page_panel' : show_prev or show_next,
                'prev' : page - 1,
                'next' : page + 1,
                'max_page' : max_page,
                })

        self.render(self.theme.postlist_page)

class PostListTag(PlogRequestHandler):
    @get_wrap
    def get(self):
        self.current_page = "home"
        page = 0
        show_prev = False
        show_next = False

        params = self.request.path[len(settings.app_root) + 1:].split('/')
        if len(params) == 4:
            page = int(params[3])

        import urllib2
        tag = urllib2.unquote(params[1]).decode('utf-8')

        all_posts = Post.all().filter('type = ', 'post').filter('tags =', tag)
        if not self.is_admin:
            all_posts.filter('pub_type = ', 'public')

        max_page = (post_count(tag) - 1) / config.posts_per_page
        posts = all_posts.order('-date').fetch(config.posts_per_page, offset = page * config.posts_per_page)

        show_prev = not (page == 0)
        show_next = not (page == max_page)

        if not posts:
            self.error_404()

        self.template_values.update({
                'tag' : tag,
                'posts' : posts,
                'show_prev' : show_prev,
                'show_next' : show_next,
                'show_page_panel' : show_prev or show_next,
                'prev' : page - 1,
                'next' : page + 1,
                'max_page' : max_page,
                })

        self.render(self.theme.postlist_page)

class ViewPost(PlogRequestHandler):
    @get_wrap
    def get(self):
        self.current_page = "home"
        postid = self.request.path[len(settings.app_root) + len('/post/'):]
        post = Post.get_by_id(int(postid))
        comments = Comment.all().filter('post = ', post).order('date')

        if not self.is_admin and post and post.pub_type == 'private':
            post = None

        if not post:
            self.error_404()
        else:
            update_hits(post)
            self.template_values.update({
                    'post' : post,
                    'comments' : comments,
                    })

            self.render(self.theme.viewpost_page)

class Feed(PlogRequestHandler):
    def get(self):
        feed_type = self.param('type')
        if feed_type.lower() == 'atom' or feed_type.lower() == 'atom1':
            feed_type = 'atom1'
        else:
            feed_type = 'rss2'

        tag = self.param('tag')

        feed_title = config.plog_title

        if tag:
            feed_title += u' - Tag: ' + tag
            posts = Post.all().filter('type = ', 'post').filter('tags = ', tag).order('-date').fetch(config.rss_posts)
        else:
            posts = Post.all().filter('type = ', 'post').order('-date').fetch(config.rss_posts)

        if feed_type == 'rss2':
            feed = Rss201rev2Feed(
                    title = feed_title,
                    link = config.default_host + settings.home_page,
                    description= u'latest %d posts of %s' % (min(len(posts), config.rss_posts), config.plog_title),
                    subtitle = config.plog_subtitle
                    )
        elif feed_type == 'atom1':
            feed = Atom1Feed(
                    title = feed_title,
                    link = config.default_host + settings.home_page,
                    description = u'latest %d posts of %s' % (min(len(posts), config.rss_posts), config.plog_title),
                    subtitle = config.plog_subtitle
                    )

        for post in posts:
            post_url = '%s%s/post/%d' % (config.default_host, settings.app_root, post.key().id()) # TODO permernent URL

            if feed_type == 'rss2':
                feed.add_item(
                        title = post.title,
                        author_email = post.author.nickname(),    # in django's implementation of rss2,
                                                                # if author email not set,
                                                                # author will not appear in feed,
                                                                # but we don not want leak author's email.
                        link = post_url,
                        description = post.content,
                        pubdate = post.date,
                        unique_id = post_url,
                        categories = post.tags
                        )
            elif feed_type == 'atom1':
                feed.add_item(
                        title = post.title,
                        author_name = post.author.nickname(),
                        link = post_url,
                        description = post.content,
                        pubdate = post.date,
                        unique_id = post_url,
                        categories = post.tags
                        )

        self.response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
        from StringIO import StringIO
        buffer = StringIO()
        feed.write(buffer, 'utf-8')
        feed_xml = buffer.getvalue()
        buffer.close()
        self.write(feed_xml)

# by jfo
orig_referer = ""
class postLogInOut(PlogRequestHandler):
    def get(self):
        global orig_referer
        v = self.param("v")

        if v == "login":
            ccLuckHandler.update_luck(str(self.user))
        elif v == "logout":
            pass

        url = orig_referer
        orig_referer = ""
        self.redirect(url)

class LogInOut(PlogRequestHandler):
    def get(self):
        global orig_referer
        orig_referer = self.referer
        self.referer = self.request.host_url + settings.app_root + "/postloginout"
        if self.request.path == '%s/login' % settings.app_root:
            self.referer += "?v=login"
            self.redirect(self.get_login_url(True))

        if self.request.path == '%s/logout' % settings.app_root:
            ccLuckHandler.update_luck(str(self.user))
            self.referer += "?v=logout"
            self.redirect(self.get_logout_url(True))

class Download(PlogRequestHandler):
    def get(self):
        filename = self.request.path[len(settings.app_root) + len('/upload/'):]
        split = filename.rfind('.')
        if split == -1:
            name, ext = filename, ''
        else:
            name = filename[:split]
            ext = filename[split + 1:]

        file = UploadFile.get(db.Key(name))
        if not file:
            self.error_404()
        elif file.ext != ext:
            self.error_404()
        else:
            ext = '.' + ext
            mimetype = 'application/octet-stream'
            if types_map.has_key(ext):
                mimetype = types_map[ext]
            self.response.headers['Content-Type'] = mimetype
            self.response.headers['Content-Disposition'] = 'inline; filename="' + file.orig_name.encode('utf-8') + '"'
            self.write(file.data)

# }}}

# {{{ Admin
class Configure(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            self.current_page = "config"

            password = ""
#            admin = Admin.all().filter('user = ', self.user.user).get()
#            if admin:
#                password = admin.api_password

            config_form = ConfigForm(instance = config)
            self.template_values.update({
                'config_form' : config_form,
                'password' : password,
                })

            self.render(self.theme.config_page)

    def post(self):
        if self.chk_admin():
            config_form = ConfigForm(data = self.request.POST, instance = config)
            if config_form.is_valid():
                config_form.save(commit=False)
                config.put()

                reconfig()
                regenerate_url_mapping()
                settings.theme = Theme(config.theme)

                memcache.notify_update('config')
                self.redirect(settings.home_page)
            else:
                self.template_values.update({
                    'config_form' : config_form,
                    })

                self.render(self.theme.config_page)


class Upload(PlogRequestHandler):
    def post(self):
        if self.chk_admin():
            filename = self.param('filename')
            fileext = self.param('fileext')
            data = self.param('upfile')
            UploadFile(orig_name = filename, ext = fileext, data = data).put()
            memcache.notify_update('upload')
            self.redirect('%s/admin/filemanager' % settings.app_root)

class FileManager(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            self.current_page = "upload"
            files = UploadFile.all().order('-date')
            self.template_values.update({
                'files' : files,
                })
            self.render(self.theme.filemanager_page)

    def post(self): # delete files
        if self.chk_admin():
            delids = self.request.POST.getall('del')
            if delids:
                for id in delids:
                    file = UploadFile.get_by_id(int(id))
                    file.delete()
                    memcache.notify_update('upload')
            self.redirect('%s/admin/filemanager' % settings.app_root)

class LinkManager(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            self.current_page = "links"
            if self.param('tag'):
                links = Link.all().filter('tags = ', self.param('tag')).order('text')
            else:
                links = Link.all().order('text')

            self.template_values.update({
                'links' : links,
                })
            self.render(self.theme.linkmanager_page)

    def post(self):
        if self.chk_admin():
            try:
                action = self.param('action')
                if action == 'new':
                    tags = split_tags(self.param('linktags'))
                    if not tags:
                        tags = [' ']
                    link = Link(
                            url = self.param('url'), text = self.param('text'),
                            description = self.param('description'),
                            tags = tags)
                    link.put()
                elif action == 'edit':
                    link = Link.get_by_id(int(self.param('linkid')))
                    link.text = self.param('text')
                    link.url = self.param('url')
                    link.description = self.param('description')
                    link.tags = split_tags(self.param('linktags'))
                    link.put()
                elif action == 'delete':
                    linkids = self.request.POST.getall('linkid')
                    for linkid in linkids:
                        link = Link.get_by_id(int(linkid))
                        link.delete()

                memcache.notify_update('link')
            except Exception, e:
                raise e

            self.redirect(self.referer)

class ReGeneratePassword(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            password = self.param("passwd")
            if not password:
                password = regenerate_password(self.user.user)
            else:
                password = generate_password(self.user.user, password)
            logging.debug("jfo:regenerate:password:" + password)
            self.response.headers['Content-Type'] = 'text/plain'
            self.write(password)

class ViewMemcacheStats(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            table_memcache_status = render_dict(memcache.memcache.get_stats())
            table_obj_last_modify = render_dict(memcache.obj_last_modify)
            table_theme_mapping = render_dict(settings.theme.mapping_cache)

            self.write('''
            <h1>Memcache Status</h1>%s
            <h1>Last Modify</h1>%s
            <h1>Theme Mapping</h1>%s
            ''' % (table_memcache_status, table_obj_last_modify, table_theme_mapping))

class ViewMemcacheContent(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            content = memcache.memcache.get(self.param('key'))
            self.write('<textarea style="width:100%%;height:100%%">%s</textarea>' % cgi.escape(str(content)))

class CheckDataIntegrity(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            msgs = check_data_integrity()
            if not msgs:
                self.write('Great! Data seems all good!')
            else:
                for msg in msgs:
                    self.write(msg + '<br />')
                self.write('<form method="post"><input type="submit" value="fix them all!" /></form>')

    def post(self): # fix
        if self.chk_admin():
            check_data_integrity(True)
            memcache.memcache.flush_all()
            self.redirect('checkdataintegrity')

class FlushMemcache(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            memcache.memcache.flush_all()
            self.redirect(settings.home_page)


# TODO remove this handler
class ImportBlogRoll(PlogRequestHandler):
    class BlogRoll(db.Model):
        text = db.StringProperty()
        url = db.LinkProperty()
        description = db.StringProperty()

    def get(self):
        if self.chk_admin():
            for link in ImportBlogRoll.BlogRoll.all():
                Link(text = link.text, url = link.url, description = link.description, tags = ['Blogroll']).put()
                link.delete()

            self.redirect('linkmanager')

class FixDefaultPageType(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            for post in Post.all():
                post.put()

            self.redirect(settings.home_page)
#}}}

# {{{ Theme Files
class GetFile(PlogRequestHandler):
    def get(self):
        cwd = os.getcwd()
        theme_path = os.path.join(cwd, 'themes')
        max_age = 600  #expires in 10 minutes

        request_path = self.request.path[len(settings.app_root) + len('/themes/'):]
        server_path = os.path.normpath(os.path.join(cwd, 'themes', request_path))
        last_config_time = memcache.obj_last_modify['config'].replace(microsecond=0)

        if self.request.if_modified_since and self.request.if_modified_since.replace(tzinfo=None) >= last_config_time:
            self.response.headers['Date'] = format_date(datetime.datetime.utcnow())
            self.response.headers['Last-Modified'] = format_date(last_config_time)
            cache_expires(self.response, max_age)
            self.response.set_status(304)
            self.response.clear()

        elif server_path.startswith(theme_path):
            ext = os.path.splitext(server_path)[1]
            if types_map.has_key(ext):
                mime_type = types_map[ext]
            else:
                mime_type = 'application/octet-stream'
            try:
                self.response.headers['Content-Type'] = mime_type
                self.response.headers['Last-Modified'] = format_date(last_config_time)
                cache_expires(self.response, max_age)
                self.response.out.write(open(server_path, 'rb').read())
            except Exception, e:
                logging.info(e)
                self.error_404()
        else:
            self.error_404()

#}}}

# {{{ API
class CallApi(PlogRequestHandler):
    def get(self):
        self.write('<h1>please use POST to use APIs</h1>')

    def post(self):
        request = self.request.body
        response = dispatcher._marshaled_dispatch(request)
        self.write(response)

#}}}

# {{{ Not Found
class NotFound(PlogRequestHandler):
    def get(self):
        self.error_404()
# }}}



class ShowIPHandler(PlogRequestHandler):
    def get(self):
        order = self.request.get('order')
        if (order == 'byip'):
            ips = IPDataBlog.all().order('ip')
        elif (order == 'byuri'):
            ips = IPDataBlog.all().order('uri')
        else:
            ips = IPDataBlog.all().order('-atime')
        self.template_values.update({
            'ips': ips,
        })
        self.render(self.theme.viewip_page)

class ClearIPHandler(PlogRequestHandler):
    def get(self):
        ips = IPDataBlog.all()
        for ip in ips:
            ip.delete()
        logging.info("all ips are cleared")
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Cleared success')

class DeleteIPHandler(PlogRequestHandler):
    def get(self):
        id = long(self.request.get('id'))
        item = IPDataBlog.get_by_id(id)
        if(item):
            item.delete()
        self.redirect('%s/track_ip' % settings.app_root)

class LocateIPHandler(PlogRequestHandler):
    def get(self):
        ip = self.param("ip")
        f = UploadFile.all().filter("orig_name = ", "QQWry.Dat").get()
        if ip and f:
            i = IPInfo(f.data)
            (c, a) = i.getIPAddr(ip)
            self.write("%s/%s" % (c.decode("utf-8"), a.decode("utf-8")))


#class IPData(db.Model):
#    ip = db.StringProperty(required=True)
#    uri = db.StringProperty(required=True)
#    atime = db.DateTimeProperty(auto_now_add=True)
#
#class Clear(PlogRequestHandler):
#    def get(self):
#        num = 100
#        n = self.request.get('n')
#        if n:
#            num = int(n)
#        q = db.GqlQuery("SELECT * FROM IPData")
#        results = q.fetch(num)
#        for result in results:
#            result.delete()
#
##        ips = IPData.all()
##        for ip in ips:
##            ip.delete()
#        self.response.headers['Content-Type'] = 'text/plain'
#        self.response.out.write('Cleared success')


class Search(PlogRequestHandler):
    def get(self):
        s = self.param('s')
        #query = Post.all().search(s).order("-date")
        #for q in query:
        #    logging.info("%s | %s" % (q.title, q.pub_type))
        self.redirect(settings.home_page)


class Image:
    class Container:
        def __init__(self):
            self.L = []

        def __iter__(self):
            return self.L.__iter__()

        def __str__(self):
            s = "["
            for i in self.L:
                s += '"' + str(i) + '"' + ", ";
            s += "]"
            return s

        def append(self, i):
            self.L.append(i)

        def clear(self):
            logging.info("clear:" + str(self))
            self.L = []
            return ""

    images = Container()

    def __init__(self, uploadfile):
        self.uploadfile = uploadfile

    def __str__(self):
        return self.uploadfile.orig_name.encode('utf-8')

    def get_thumb_url(self):
        return "/upload/%s" % (self.uploadfile.name())

    def title(self):
        return self.uploadfile.orig_name

class UploadPic(PlogRequestHandler):
    def get(self):
        if self.chk_admin():
            logging.info(self.request.uri)
            finished = self.param('finished')
            if finished:
                Image.images.clear()
                self.template_values.update({
                    'finished' : "finished",
                    })
            else:
                self.template_values.update({
                    'images' : Image.images,
                    })
            self.render(self.theme.upload_pic)

    def post(self):
        if self.chk_admin():
            filename = self.param('filename')
            fileext = self.param('fileext')
            data = self.param('upfile')
            f = UploadFile(orig_name = filename, ext = fileext, data = data)
            f.put()
            memcache.notify_update('upload')
            Image.images.append(Image(uploadfile = f))
            self.redirect('%s/admin/uploadpic' % settings.app_root)

class Sitemap(PlogRequestHandler):
    def get(self):
        posts = Post.all().filter('pub_type = ', 'public').order("-date")
        html = ""
        for post in posts:
            html += self.request.host_url + settings.home_page + "post/" + str(post.key().id()) + '\n'
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(html)

class Wish(db.Model):
#    name = db.StringProperty()
#    content = db.StringProperty()
#    date = db.DateTimeProperty(auto_now_add=True)

    def __init__(self, id, name, content, date):
        self.id = id
        self.name = name
        self.content = content
        self.date = date

class WishWall(PlogRequestHandler):
    def get(self):
        self.current_page = "wish"
        self.template_values.update({
            'wishes': [
                Wish(001, "jfo", "Oh, hi ~", "today"),
                Wish(003, "jof", "aha, welcome", "now"),
                ]
        })
        self.render(self.theme.wishwall_page)


class ccLuckHandler(PlogRequestHandler):
    T = 7    #days

    @staticmethod
    def update_luck(name):
        logging.debug("*******:" + name)
        if name and name != "" and name.lower() != "none":
            lucks = ccLuck.all().filter('fr = ', name).filter('status = ', "keep")
            for luck in lucks:
                t = datetime.datetime.utcnow() + datetime.timedelta(days = luck.delta)
                luck.deadtime = t
                luck.put()

    def get(self):
        self.current_page = "ccluck"
        delete = self.param("del")

        logging.debug("*****:" + str(self.user))
        lucks = ccLuck.all().filter("fr = ", str(self.user)).order("-date")
        if delete.lower() == "all":
            for luck in lucks:
                luck.delete()
        elif delete != "":
            luck = ccLuck.get_by_id(int(delete))
            if luck:
                luck.delete()
        if delete != "":
            self.redirect(settings.app_root + "/ccluck")
            return

        lucks = ccLuck.all().filter('fr = ', str(self.user)).order("-date")
        self.template_values.update({
            'lucks': lucks,
        })
        self.render(self.theme.ccluck_page)

    def post(self):
        to = self.param("sendto")
        content = self.param("sendwhat")
        #date = self.param("deadline_date")
        #time = self.param("deadline_time")
        delta = self.param("days")

        t = datetime.datetime.utcnow()
        try:
            #end = datetime.datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
            end = t + datetime.timedelta(days = int(delta))
        except:
            end = t + datetime.timedelta(days = self.T)
            pass
        logging.debug("*****:" + str(end))
        aLuck = ccLuck(to = to, content = content, fr = str(self.user), date = t, deadtime = end, delta = int(delta))
        aLuck.put()

        self.redirect('%s/ccluck' % settings.app_root)

class ccCheckTimeoutHandler(PlogRequestHandler):
    def get(self):
        lucks = ccLuck.all().order("-date")
        for luck in lucks:
            t = datetime.datetime.utcnow()
#            mail.send_mail(sender="j_fo@163.com",
#                      to="jfojfo@gmail.com",
#                      subject="Your account has been approved",
#                      body="oooooooooooops")
            if t > luck.deadtime and luck.status == "keep":
                logging.debug("*****: sending %s->%s(%s) @ %s" % (luck.fr, luck.to, luck.content, str(t)))

                try:
                    msg = mail.EmailMessage()
                    msg.sender = "jfo.appspot.com@gmail.com"
                    msg.subject = (u'A Wishing Luck From "%s"' % (luck.fr)).encode('utf-8')
                    #msg.subject = 'A Wishing Luck From <%s>' % (luck.fr)
                    msg.to = [luck.to]
                    msg.body = luck.content
                    msg.body += '\n\n----------------------------------------------\n'
                    msg.body += 'For more infomation, please visit "http://jfo.appspot.com/ccluck" \n'
                    msg.body = msg.body.encode('utf-8')
                    #msg.body = luck.content
                    msg.send()
                    luck.status = "sent"
                    luck.put()
                except Exception, e:
                    logging.error(e)
                    raise e

        self.redirect('%s/ccluck' % settings.app_root)

class ProjectHandler(PlogRequestHandler):
    pass

class TestHandler(PlogRequestHandler):
    def get(self):
        msg = mail.EmailMessage()
        msg.sender = "zjuwufan@gmail.com"
        msg.subject = "A testing mail"
        msg.to = ["jfojfo@gmail.com", "jofsky@gmail.com"]
        msg.body = "This is a testing email ..."
        msg.send()
        self.response.out.write("Ok")


#}}}


# {{{ url mapping

url_mapping = []
url_mapping_admin = []

def regenerate_url_mapping():
    global url_mapping
    global url_mapping_admin

    url_mapping = [
            # plog
            ('/', PostList),
            ('%s' % settings.app_root, PostList),
            ('%s/' % settings.app_root, PostList),
            ('%s/post/\\d+' % settings.app_root, ViewPost),
            ('%s/post/page/\\d+' % settings.app_root, PostList),
            ('%s/tag/.+/page/\\d+' % settings.app_root, PostListTag),
            ('%s/tag/.+' % settings.app_root, PostListTag),
            ('%s/newcomment' % settings.app_root, NewComment),
            ('%s/deletecomment' % settings.app_root, DeleteComment),
            ('%s/feed' % settings.app_root, Feed),
            ('%s/login' % settings.app_root, LogInOut),
            ('%s/logout' % settings.app_root, LogInOut),
            ('%s/postloginout' % settings.app_root, postLogInOut),
            ('%s/upload/.+' % settings.app_root, Download),
            # theme files
            ('%s/themes/[\\w\\-]+/templates/.*' % settings.app_root, NotFound),
            ('%s/themes/[\\w\\-]+/.+' % settings.app_root, GetFile),
            # api
            ('%s/api/xml-rpc' % settings.app_root, CallApi),
            # by jfo
            ('%s/track_ip' % settings.app_root, ShowIPHandler),
            ('%s/track_ip/' % settings.app_root, ShowIPHandler),
            ('%s/track_ip/clear' % settings.app_root, ClearIPHandler),
            ('%s/track_ip/delete' % settings.app_root, DeleteIPHandler),
            ('%s/track_ip/L' % settings.app_root, LocateIPHandler),
            #('%s/clear' % settings.app_root, Clear),
            ('%s/search/' % settings.app_root, Search),
            ('%s/sitemap.txt' % settings.app_root, Sitemap),
            ('%s/wishwall' % settings.app_root, WishWall),
            ('%s/ccluck' % settings.app_root, ccLuckHandler),
            ('%s/ccluckcheck' % settings.app_root, ccCheckTimeoutHandler),
            ('%s/page/\\d+' % settings.app_root, ViewPost),
            ('%s/project' % settings.app_root, ProjectHandler),
            ('%s/test' % settings.app_root, TestHandler),
            ]

    url_mapping_admin = url_mapping[:]
    url_mapping_admin += [
            # admin
            ('%s/admin/newpost' % settings.app_root, NewPost),
            ('%s/admin/editpost/\\d+' % settings.app_root, EditPost),
            ('%s/admin/deletepost' % settings.app_root, DeletePost),
            ('%s/admin/regeneratepassword' % settings.app_root, ReGeneratePassword),
            ('%s/admin/memcachestats' % settings.app_root, ViewMemcacheStats),
            ('%s/admin/memcachecontent' % settings.app_root, ViewMemcacheContent),
            ('%s/admin/checkdataintegrity' % settings.app_root, CheckDataIntegrity),
            ('%s/admin/flushmemcache' % settings.app_root, FlushMemcache),
            ('%s/admin/config' % settings.app_root, Configure),
            ('%s/admin/upload' % settings.app_root, Upload),
            ('%s/admin/uploadpic' % settings.app_root, UploadPic),
            ('%s/admin/filemanager' % settings.app_root, FileManager),
            ('%s/admin/linkmanager' % settings.app_root, LinkManager),
            ('%s/admin/addlink' % settings.app_root, LinkManager),
            ('%s/admin/dellink' % settings.app_root, LinkManager),
            ('%s/admin/importblogroll' % settings.app_root, ImportBlogRoll),
            ('%s/admin/FixDefaultPageType' % settings.app_root, FixDefaultPageType),
            ]
    url_mapping.append(('.*', NotFound))
    url_mapping_admin.append(('.*', NotFound))
    logging.info('url mapping regenerated')

regenerate_url_mapping()
# }}}

def main():
    if users.is_current_user_admin():
        logging.debug('admin')
        mapping = url_mapping_admin
    else:
        logging.debug('user')
        mapping = url_mapping

    webapp.template.register_template_library('filter')
    application = webapp.WSGIApplication(
            mapping,
            debug=False)
    wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()

