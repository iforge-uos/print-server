
class Option:
    name: str
    short: str = None
    desc: str = None
    secret: bool = False

    def __init__(self, name, short=None, desc=None, secret=False):
        self.name = name.lower()
        if short:
            self.short = short.lower()
        if desc:
            self.desc = desc.lower()
        if secret:
            self.secret = secret

    def to_list(self):
        if self.short:
            return [self.name, self.short]
        else:
            return [self.name]

    def __repr__(self):
        return f"Option({self.name}, short={self.short}, desc={self.desc})"

    def __str__(self):
        if self.desc:
            return f"{self.short:2s}  -  {self.name:12s}  -  {self.desc}"
        else:
            return f"{self.short:2s}  -  {self.name:12s}"

def get_choice(prompt, options, display_options=True, display_secrets=False):
    # Not case-sensitive
    """
    options: dict{name, short=None}
    """
    print(f"{prompt}")

    if display_options:
        print(f"Options:")
        for option in options:
            if display_secrets:
                print(option)
            elif not option.secret:
                print(option)
    # else:
    #     print("Options list disabled, hope you know what you're doing ;)")

    inp_str = input(f">> ").lower()

    while True:
        for opt in options:
            if inp_str in opt.to_list():
                return opt.name

        print(f"{prompt}")

        if display_options:
            print(f"Options:")
            for option in options:
                if display_secrets:
                    print(option)
                elif not option.secret:
                    print(option)

        inp_str = input(f">> ").lower()
