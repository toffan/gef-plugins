# File is sourced by gdb, after gef, which defines multiple variables
# gdb, gef
# @only_if_gdb_running, @parse_arguments,
# GenericCommand, register_external_command
# warn, ok
import pickle


@register
class FulldumpCommand(GenericCommand):
    """Dump memory and registers of the current execution."""

    _cmdline_ = "fulldump"
    _syntax_ = f"{_cmdline_} [FILENAME]"
    _example_ = f"{_cmdline_} keygen.dump"

    def __init__(self) -> None:
        super().__init__(prefix=False, complete=gdb.COMPLETE_LOCATION)
        return

    @only_if_gdb_running
    @parse_arguments({"filename": "fulldump.dump"}, {})
    def do_invoke(self, _: list[str], **kwargs) -> None:
        args = kwargs["arguments"]

        memory = []
        for sect in gef.memory.maps:
            size = sect.page_end - sect.page_start
            try:
                raw = gef.memory.read(sect.page_start, size)
                memory.append(
                    {
                        "start": sect.page_start,
                        "end": sect.page_end,
                        "memory": raw,
                        "permission": str(sect.permission),
                        "name": sect.path,
                    }
                )
            except gdb.MemoryError as e:
                warn(f"{e} (section {sect.path})")

        # GPR
        regs = {regname: gef.arch.register(regname) for regname in gef.arch.registers}

        # XMM
        if gef.arch.arch == X86.arch:
            xmm_cnt = 8 if gef.arch.mode == "32" else 16

            for i in range(xmm_cnt):
                res = gdb.execute(f"info registers xmm{i}", to_string=True)
                # Returns something like to following
                # xmm0           {
                #   ...
                #   uint128 = 0xff000000000000000000000000000000
                # }
                xmm = next(
                    line.strip() for line in res.splitlines() if "uint128 =" in line
                )
                xmm = int(xmm.split()[2], 16)
                regs[f"xmm{i}"] = xmm

        dump = (regs, memory)

        with open(args.filename, "wb") as fd:
            pickle.dump(dump, fd)

        ok(f"Full dump saved into {args.filename}")


FulldumpCommand()
