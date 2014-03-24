mp.set_property("audio","no")
mp.set_property("pause","yes")

namespace=string.gsub(mp.get_script_name(),'lua/','')
num_frames=tonumber(mp.get_opt(string.format("%s.num_frames",namespace)))
if not num_frames then
   num_frames=11
end

frames_shown=0
function advance()
   frames_shown=frames_shown+1
   if frames_shown<num_frames then
      mp.command(string.format("seek %g absolute-percent",100*(frames_shown+1)/num_frames))
      -- effectively call advance() recursively since this generates a playback-restart event
   else
      mp.command("quit")
   end
end
mp.register_event("playback-restart",advance)
