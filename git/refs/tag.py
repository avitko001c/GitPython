from .reference import Reference
from git.exc import GitCommandError

__all__ = ["TagReference", "Tag"]


class TagReference(Reference):

    """Class representing a lightweight tag reference which either points to a commit
    ,a tag object or any other object. In the latter case additional information,
    like the signature or the tag-creator, is available.

    This tag object will always point to a commit object, but may carry additional
    information in a tag object::

     tagref = TagReference.list_items(repo)[0]
     print(tagref.commit.message)
     if tagref.tag is not None:
        print(tagref.tag.message)"""

    __slots__ = ()
    _common_path_default = "refs/tags"

    @property
    def commit(self):
        """:return: Commit object the tag ref points to

        :raise ValueError: if the tag points to a tree or blob"""
        obj = self.object
        while obj.type != 'commit':
            if obj.type == "tag":
                # it is a tag object which carries the commit as an object - we can point to anything
                obj = obj.object
            else:
                raise ValueError(("Cannot resolve commit as tag %s points to a %s object - " +
                                  "use the `.object` property instead to access it") % (self, obj.type))
        return obj

    @property
    def tag(self):
        """
        :return: Tag object this tag ref points to or None in case
            we are a light weight tag"""
        obj = self.object
        if obj.type == "tag":
            return obj
        return None

    # make object read-only
    # It should be reasonably hard to adjust an existing tag
    object = property(Reference._get_object)

    @classmethod
    def create(cls, repo, tag, push=False, ref='HEAD', message=None, force=False, **kwargs):
        """Create a new tag reference.
        :param push:
            If True, push the tag after creation with a force.
            
        :param tag:
            The name of the tag, i.e. 1.0 or releases/1.0.
            The prefix refs/tags is implied

        :param ref:
            A reference to the object you want to tag. It can be a commit, tree or
            blob.

        :param message:
            If not None, the message will be used in your tag object. This will also
            create an additional tag object that allows to obtain that information, i.e.::

                tagref.tag.message

        :param force:
            If True, to force creation of a tag even though that tag already exists.

        :param kwargs:
            Additional keyword arguments to be passed to git-tag

        :return: A new TagReference"""
        args = (tag, ref)
        if message:
            kwargs['m'] = message
        if force:
            kwargs['f'] = True
        repo.git.tag(*args, **kwargs)
        if push:
            if message:
                del kwargs['m']
            try:
                repo.git.push('origin', tag, **kwargs)
            except GitCommandError as err:
                if err.status == 1:
                    pass
                return False

        return TagReference(repo, "%s/%s" % (cls._common_path_default, tag))

    @classmethod
    def delete(cls, repo, push=False, *tags, **kwargs):
        """Delete the given existing tag or tags"""
        repo.git.tag("-d", *tags)
        if push:
            kwargs['d'] = True
            for tag in tags:
                try:
                    repo.git.push('origin', tag, **kwargs)
                except GitCommandError as err:
                    if err.status == 1:
                       pass
                    return False


# provide an alias
Tag = TagReference
