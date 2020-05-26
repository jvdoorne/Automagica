import random
import string


class Node:
    def __init__(self, x=None, y=None, uid=None, label=None):
        if not uid:
            uid = self._generate_uid(4)

        self.uid = uid

        self.label = label

        if not x:
            x = 0

        if not y:
            y = 0

        self.x = x
        self.y = y

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.uid)

    def __str__(self):
        if self.label:
            return self.label
        else:
            return self.__class__.__name__.replace("Node", "")

    def _generate_uid(self, k):
        return "".join(
            random.choices(
                string.ascii_uppercase + string.ascii_lowercase + string.digits, k=k
            )
        )

    def to_dict(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class StartNode(Node):
    def __init__(self, *args, next_node=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_node = next_node

    def get_next_node(self):
        return self.next_node

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "next_node": self.next_node,
            "label": self.label,
        }

    def run(self, bot):
        pass


class ActivityNode(Node):
    def __init__(
        self, activity, *args, next_node=None, class_=None, args_=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.activity = activity
        if not args_:
            args_ = {}
        self.args_ = args_
        self.next_node = next_node
        self.return_ = None

        if self.activity.split(".")[-2][0].isupper():
            class_ = self.activity.split(".")[-2].lower()
            if not self.args_.get("self"):
                self.args_["self"] = class_.lower()

        self.class_ = class_

    def __str__(self):
        from automagica.config import ACTIVITIES

        if self.label:
            return self.label
        else:
            return ACTIVITIES[self.activity]["name"]

    def get_next_node(self):
        return self.next_node

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "next_node": self.next_node,
            "label": self.label,
            "activity": self.activity,
            "args": self.args_,
            "class": self.class_,
        }

    def run(self, bot, on_done=None):
        args = [
            "{}={}".format(key, val)
            for key, val in self.args_.items()
            if key != "self" and val != None
        ]

        command = "# {} ({})\n".format(self, self.uid)

        if self.class_:
            module_ = ".".join(self.activity.split(".")[:-2])
            function_ = self.activity.split(".")[-1]

            command += "from {} import {}\n".format(
                module_, self.activity.split(".")[-2]
            )  # from automagica.activities import Chrome

            if function_ == "__init__":
                command += "{} = {}({})\n".format(
                    self.args_["self"], self.activity.split(".")[-2], ", ".join(args),
                )  # chrome = Chrome()

            else:
                command += "{}.{}({}, {})\n".format(
                    self.activity.split(".")[-2],
                    function_,
                    self.args_["self"],
                    ", ".join(args),
                )  # Chrome.get(chrome, 'https://google.com")

        else:
            module_ = ".".join(self.activity.split(".")[:-1])
            function_ = self.activity.split(".")[-1]

            command += "from {} import {}\n".format(module_, function_)
            if self.return_:
                command += "{} = {}({})\n".format(
                    self.return_, function_, ", ".join(args)
                )
            else:
                command += "{}({})\n".format(function_, ", ".join(args))

        bot.run(command, on_done=on_done)


class IfElseNode(Node):
    def __init__(self, *args, condition=None, next_node=None, else_node=None, **kwargs):
        super().__init__(**kwargs)
        self.condition = condition
        self.next_node = next_node  # True node
        self.else_node = else_node

    def get_next_node_uid(self, return_value):
        if return_value:
            return self.next_node
        else:
            return self.else_node

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "next_node": self.next_node,
            "else_node": self.else_node,
            "label": self.label,
            "condition": self.condition,
        }

    def run(self, bot, on_done=None):
        bot.run(self.condition, on_done=on_done, return_value_when_done=True)


class LoopNode(Node):
    def __init__(
        self, *args, iterable="", item="", next_node=None, loop_node=None, **kwargs
    ):
        super().__init__(**kwargs)
        self.iterable = iterable
        self.item = item
        self.loop_node = loop_node
        self.next_node = next_node

    def get_next_node(self):
        try:
            # While iterable, iterate
            return next(self.iterable)
        except StopIteration:
            # Reset iterable and go to next node
            self.iterable.seek(0)
            return self.next_node

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "iterable": self.iterable,
            "item": self.item,
            "next_node": self.next_node,
            "loop_node": self.loop_node,
            "label": self.label,
        }

    def run(self, bot, on_done=None):
        pass


class DotPyFileNode(Node):
    def __init__(
        self,
        *args,
        dotpyfile_path=None,
        next_node=None,
        on_exception_node=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.dotpyfile_path = dotpyfile_path
        self.next_node = next_node
        self.on_exception_node = on_exception_node

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "next_node": self.next_node,
            "dotpyfile_path": self.dotpyfile_path,
            "on_exception_node": self.on_exception_node,
            "label": self.label,
        }

    def run(self, bot):
        command = open(self.dotpyfile_path).read()
        bot.run(command)


class CommentNode(Node):
    def __init__(self, *args, comment=None, **kwargs):
        super().__init__(**kwargs)
        self.comment = comment

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "comment": self.comment,
            "label": self.label,
        }

    def run(self, bot):
        pass


class SubFlowNode(Node):
    def __init__(
        self,
        *args,
        subflow_path=None,
        next_node=None,
        on_exception_node=None,
        iterator=None,
        iterator_variable=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.subflow_path = subflow_path
        self.next_node = next_node
        self.on_exception_node = on_exception_node
        self.iterator = iterator
        self.iterator_variable = iterator_variable

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "next_node": self.next_node,
            "on_exception_node": self.on_exception_node,
            "subflow_path": self.subflow_path,
            "iterator": self.iterator,
            "iterator_variable": self.iterator_variable,
            "label": self.label,
        }

    def run(self, bot, on_done=None):
        from .flow import Flow

        subflow = Flow(self.subflow_path)
        subflow.run(bot)


class PythonCodeNode(Node):
    def __init__(
        self, *args, code=None, next_node=None, on_exception_node=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.code = code
        self.next_node = next_node
        self.on_exception_node = on_exception_node

    def to_dict(self):
        return {
            "uid": self.uid,
            "x": self.x,
            "y": self.y,
            "type": self.__class__.__name__,
            "next_node": self.next_node,
            "code": self.code,
            "on_exception_node": self.on_exception_node,
            "label": self.label,
        }

    def run(self, bot, on_done=None):
        bot.run(self.code, on_done=on_done)