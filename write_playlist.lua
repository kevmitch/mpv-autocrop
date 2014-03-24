require 'mp.msg'
mp.set_property("audio","no")
mp.set_property("pause","yes")

namespace=string.gsub(mp.get_script_name(),'lua/','')
opt_name=string.format("%s.out_file",namespace)
out_file=mp.get_opt(opt_name)

if not out_file then
   out_file="mpv_playlist"
end

local f = io.open(out_file,"w")
if not f then
   mp.msg.error(string.format("couldn't open %s",out_file))
else
   playlist_count=mp.get_property("playlist-count")
   for i=1,playlist_count do
      filename=mp.get_property(string.format("playlist/%d/filename",i-1))
      f:write(filename)
      f:write("\0")
   end
   f:close()
end
mp.command("quit")
